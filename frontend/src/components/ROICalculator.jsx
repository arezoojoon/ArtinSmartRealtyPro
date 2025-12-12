/**
 * ROI Calculator Component
 * Calculate real ROI based on actual property data from database
 */

import React, { useState, useEffect } from 'react';
import {
    Calculator,
    TrendingUp,
    DollarSign,
    Home,
    Calendar,
    Percent,
    Download,
    RefreshCw
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const api = {
    async get(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    },
    
    async post(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }
};

const ROICalculator = ({ propertyId = null, onClose = null }) => {
    const [properties, setProperties] = useState([]);
    const [selectedProperty, setSelectedProperty] = useState(null);
    const [loading, setLoading] = useState(true);
    const [calculating, setCalculating] = useState(false);
    
    // ROI Results
    const [roiResults, setRoiResults] = useState(null);
    
    // Manual inputs (for properties without data)
    const [manualInputs, setManualInputs] = useState({
        purchasePrice: 0,
        rentalIncome: 0,
        annualExpenses: 0,
        mortgagePayment: 0,
        holdingPeriod: 5
    });
    
    useEffect(() => {
        fetchProperties();
    }, []);
    
    useEffect(() => {
        if (propertyId && properties.length > 0) {
            const prop = properties.find(p => p.id === propertyId);
            if (prop) {
                setSelectedProperty(prop);
                calculateROI(prop);
            }
        }
    }, [propertyId, properties]);
    
    const fetchProperties = async () => {
        try {
            const response = await api.get('/api/properties?limit=100');
            setProperties(response.properties || []);
        } catch (error) {
            console.error('Failed to fetch properties:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const calculateROI = async (property) => {
        setCalculating(true);
        
        try {
            // Get property financial data
            const price = property.price || manualInputs.purchasePrice;
            const monthlyRent = property.monthly_rent || (manualInputs.rentalIncome / 12);
            const annualRent = monthlyRent * 12;
            
            // Calculate expenses (estimate if not available)
            const serviceFee = property.service_fee_annual || (price * 0.01); // 1% of price
            const maintenanceCost = price * 0.005; // 0.5% of price per year
            const insuranceCost = price * 0.002; // 0.2% of price per year
            const propertyTax = 0; // No property tax in Dubai
            const vacancyLoss = annualRent * 0.05; // 5% vacancy rate
            
            const totalAnnualExpenses = serviceFee + maintenanceCost + insuranceCost + vacancyLoss;
            
            // Net Operating Income (NOI)
            const noi = annualRent - totalAnnualExpenses;
            
            // Cash-on-Cash Return (assuming 20% down payment)
            const downPayment = price * 0.2;
            const loanAmount = price * 0.8;
            const interestRate = 0.05; // 5% interest
            const monthlyMortgage = (loanAmount * (interestRate / 12)) / (1 - Math.pow(1 + (interestRate / 12), -360));
            const annualMortgage = monthlyMortgage * 12;
            
            const cashFlow = noi - annualMortgage;
            const cashOnCashReturn = (cashFlow / downPayment) * 100;
            
            // Cap Rate
            const capRate = (noi / price) * 100;
            
            // Gross Rental Yield
            const grossYield = (annualRent / price) * 100;
            
            // Net Rental Yield
            const netYield = (noi / price) * 100;
            
            // Appreciation (Dubai average ~5-7% per year)
            const appreciationRate = 0.06;
            const futureValue = price * Math.pow(1 + appreciationRate, manualInputs.holdingPeriod);
            const totalAppreciation = futureValue - price;
            
            // Total ROI over holding period
            const totalCashFlow = cashFlow * manualInputs.holdingPeriod;
            const totalReturn = totalCashFlow + totalAppreciation;
            const totalROI = (totalReturn / downPayment) * 100;
            
            setRoiResults({
                property_name: property.title || 'Custom Property',
                property_location: property.location || 'Dubai',
                
                // Purchase Info
                purchase_price: price,
                down_payment: downPayment,
                loan_amount: loanAmount,
                
                // Income
                monthly_rent: monthlyRent,
                annual_rent: annualRent,
                
                // Expenses
                service_fee: serviceFee,
                maintenance: maintenanceCost,
                insurance: insuranceCost,
                vacancy_loss: vacancyLoss,
                total_expenses: totalAnnualExpenses,
                
                // Mortgage
                monthly_mortgage: monthlyMortgage,
                annual_mortgage: annualMortgage,
                
                // Returns
                noi: noi,
                annual_cash_flow: cashFlow,
                monthly_cash_flow: cashFlow / 12,
                
                // Metrics
                gross_yield: grossYield,
                net_yield: netYield,
                cap_rate: capRate,
                cash_on_cash_return: cashOnCashReturn,
                
                // Long-term
                holding_period: manualInputs.holdingPeriod,
                future_value: futureValue,
                total_appreciation: totalAppreciation,
                total_cash_flow: totalCashFlow,
                total_return: totalReturn,
                total_roi: totalROI,
                annualized_roi: totalROI / manualInputs.holdingPeriod
            });
            
        } catch (error) {
            console.error('ROI calculation error:', error);
            alert('Failed to calculate ROI');
        } finally {
            setCalculating(false);
        }
    };
    
    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-AE', {
            style: 'currency',
            currency: 'AED',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };
    
    const formatPercent = (value) => {
        return `${value.toFixed(2)}%`;
    };
    
    const downloadReport = () => {
        if (!roiResults) return;
        
        const report = `
=== ROI ANALYSIS REPORT ===
Property: ${roiResults.property_name}
Location: ${roiResults.property_location}
Generated: ${new Date().toLocaleString()}

--- PURCHASE DETAILS ---
Purchase Price: ${formatCurrency(roiResults.purchase_price)}
Down Payment (20%): ${formatCurrency(roiResults.down_payment)}
Loan Amount: ${formatCurrency(roiResults.loan_amount)}

--- INCOME ---
Monthly Rent: ${formatCurrency(roiResults.monthly_rent)}
Annual Rent: ${formatCurrency(roiResults.annual_rent)}

--- EXPENSES ---
Service Fee: ${formatCurrency(roiResults.service_fee)}
Maintenance: ${formatCurrency(roiResults.maintenance)}
Insurance: ${formatCurrency(roiResults.insurance)}
Vacancy Loss: ${formatCurrency(roiResults.vacancy_loss)}
Total Annual Expenses: ${formatCurrency(roiResults.total_expenses)}

--- MORTGAGE ---
Monthly Payment: ${formatCurrency(roiResults.monthly_mortgage)}
Annual Payment: ${formatCurrency(roiResults.annual_mortgage)}

--- CASH FLOW ---
Net Operating Income (NOI): ${formatCurrency(roiResults.noi)}
Annual Cash Flow: ${formatCurrency(roiResults.annual_cash_flow)}
Monthly Cash Flow: ${formatCurrency(roiResults.monthly_cash_flow)}

--- KEY METRICS ---
Gross Rental Yield: ${formatPercent(roiResults.gross_yield)}
Net Rental Yield: ${formatPercent(roiResults.net_yield)}
Cap Rate: ${formatPercent(roiResults.cap_rate)}
Cash-on-Cash Return: ${formatPercent(roiResults.cash_on_cash_return)}

--- ${roiResults.holding_period}-YEAR PROJECTION ---
Future Property Value: ${formatCurrency(roiResults.future_value)}
Total Appreciation: ${formatCurrency(roiResults.total_appreciation)}
Total Cash Flow: ${formatCurrency(roiResults.total_cash_flow)}
Total Return: ${formatCurrency(roiResults.total_return)}
Total ROI: ${formatPercent(roiResults.total_roi)}
Annualized ROI: ${formatPercent(roiResults.annualized_roi)}

---
This is a projection based on current market conditions and assumptions.
Actual returns may vary. Consult with a financial advisor for personalized advice.
        `;
        
        const blob = new Blob([report], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ROI_Report_${roiResults.property_name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };
    
    if (loading) {
        return (
            <div className="flex items-center justify-center p-12">
                <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
            </div>
        );
    }
    
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                        <Calculator className="w-7 h-7 text-gold-500" />
                        ROI Calculator
                    </h2>
                    <p className="text-gray-400">Calculate return on investment based on real property data</p>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-colors"
                    >
                        Close
                    </button>
                )}
            </div>
            
            {/* Property Selection */}
            <div className="glass-card rounded-2xl p-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                    Select Property
                </label>
                <select
                    value={selectedProperty?.id || ''}
                    onChange={(e) => {
                        const prop = properties.find(p => p.id === parseInt(e.target.value));
                        setSelectedProperty(prop);
                        if (prop) calculateROI(prop);
                    }}
                    className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/50 transition-colors"
                >
                    <option value="">Choose a property...</option>
                    {properties.map(prop => (
                        <option key={prop.id} value={prop.id}>
                            {prop.title} - {formatCurrency(prop.price)} ({prop.location})
                        </option>
                    ))}
                </select>
            </div>
            
            {/* ROI Results */}
            {roiResults && (
                <div className="space-y-6">
                    {/* Key Metrics Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="glass-card rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-gray-400 uppercase">Gross Yield</span>
                                <Percent className="w-4 h-4 text-gold-500" />
                            </div>
                            <div className="text-2xl font-bold text-gold-500">
                                {formatPercent(roiResults.gross_yield)}
                            </div>
                        </div>
                        
                        <div className="glass-card rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-gray-400 uppercase">Cap Rate</span>
                                <TrendingUp className="w-4 h-4 text-green-500" />
                            </div>
                            <div className="text-2xl font-bold text-green-500">
                                {formatPercent(roiResults.cap_rate)}
                            </div>
                        </div>
                        
                        <div className="glass-card rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-gray-400 uppercase">Cash-on-Cash</span>
                                <DollarSign className="w-4 h-4 text-blue-500" />
                            </div>
                            <div className="text-2xl font-bold text-blue-500">
                                {formatPercent(roiResults.cash_on_cash_return)}
                            </div>
                        </div>
                        
                        <div className="glass-card rounded-xl p-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-gray-400 uppercase">Monthly Cash Flow</span>
                                <Calendar className="w-4 h-4 text-purple-500" />
                            </div>
                            <div className={`text-2xl font-bold ${roiResults.monthly_cash_flow >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                {formatCurrency(roiResults.monthly_cash_flow)}
                            </div>
                        </div>
                    </div>
                    
                    {/* Detailed Breakdown */}
                    <div className="glass-card rounded-2xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4">Financial Breakdown</h3>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Income */}
                            <div>
                                <h4 className="text-sm font-bold text-green-400 mb-3 uppercase">Income</h4>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Annual Rent:</span>
                                        <span className="text-white font-medium">{formatCurrency(roiResults.annual_rent)}</span>
                                    </div>
                                </div>
                            </div>
                            
                            {/* Expenses */}
                            <div>
                                <h4 className="text-sm font-bold text-red-400 mb-3 uppercase">Expenses</h4>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Service Fee:</span>
                                        <span className="text-white font-medium">{formatCurrency(roiResults.service_fee)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Maintenance:</span>
                                        <span className="text-white font-medium">{formatCurrency(roiResults.maintenance)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Insurance:</span>
                                        <span className="text-white font-medium">{formatCurrency(roiResults.insurance)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Vacancy Loss:</span>
                                        <span className="text-white font-medium">{formatCurrency(roiResults.vacancy_loss)}</span>
                                    </div>
                                    <div className="flex justify-between pt-2 border-t border-white/10">
                                        <span className="text-gray-300 font-medium">Total Expenses:</span>
                                        <span className="text-red-400 font-bold">{formatCurrency(roiResults.total_expenses)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Net Operating Income */}
                        <div className="mt-6 pt-6 border-t border-white/20">
                            <div className="flex justify-between items-center">
                                <span className="text-lg font-bold text-white">Net Operating Income (NOI):</span>
                                <span className="text-2xl font-bold text-gold-500">{formatCurrency(roiResults.noi)}</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Long-term Projection */}
                    <div className="glass-card rounded-2xl p-6 border-l-4 border-gold-500">
                        <h3 className="text-lg font-bold text-white mb-4">
                            {roiResults.holding_period}-Year Investment Projection
                        </h3>
                        
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-400">Initial Investment:</span>
                                <span className="text-white font-medium">{formatCurrency(roiResults.down_payment)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Total Cash Flow:</span>
                                <span className="text-white font-medium">{formatCurrency(roiResults.total_cash_flow)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Property Appreciation:</span>
                                <span className="text-white font-medium">{formatCurrency(roiResults.total_appreciation)}</span>
                            </div>
                            <div className="flex justify-between pt-3 border-t border-white/20">
                                <span className="text-lg font-bold text-white">Total Return:</span>
                                <span className="text-2xl font-bold text-green-500">{formatCurrency(roiResults.total_return)}</span>
                            </div>
                            <div className="flex justify-between pt-3 border-t border-white/20">
                                <span className="text-lg font-bold text-white">Total ROI:</span>
                                <span className="text-3xl font-bold text-gold-500">{formatPercent(roiResults.total_roi)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Annualized ROI:</span>
                                <span className="text-xl font-bold text-gold-400">{formatPercent(roiResults.annualized_roi)}</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Download Report */}
                    <div className="flex gap-3">
                        <button
                            onClick={downloadReport}
                            className="flex-1 px-6 py-3 btn-gold rounded-xl flex items-center justify-center gap-2"
                        >
                            <Download className="w-5 h-5" />
                            Download Full Report
                        </button>
                        <button
                            onClick={() => calculateROI(selectedProperty)}
                            className="px-6 py-3 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-xl flex items-center gap-2 transition-colors"
                        >
                            <RefreshCw className="w-5 h-5" />
                            Recalculate
                        </button>
                    </div>
                    
                    {/* Disclaimer */}
                    <div className="glass-card rounded-xl p-4 bg-yellow-500/10 border border-yellow-500/30">
                        <p className="text-xs text-yellow-200">
                            <strong>Disclaimer:</strong> This ROI calculation is based on current market conditions and standard assumptions (6% annual appreciation, 5% vacancy rate, 5% mortgage interest). Actual returns may vary based on market conditions, property management, and other factors. This is not financial advice. Consult with a qualified financial advisor before making investment decisions.
                        </p>
                    </div>
                </div>
            )}
            
            {!roiResults && selectedProperty === null && (
                <div className="glass-card rounded-xl p-12 text-center">
                    <Calculator className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Select a Property</h3>
                    <p className="text-gray-400">
                        Choose a property from the dropdown above to calculate ROI
                    </p>
                </div>
            )}
        </div>
    );
};

export default ROICalculator;

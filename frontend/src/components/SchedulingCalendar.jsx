/**
 * Artin Smart Realty - Scheduling Calendar Component
 * Monthly calendar with availability slots and upcoming appointments
 * REAL API INTEGRATION
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    ChevronLeft,
    ChevronRight,
    Plus,
    Clock,
    User,
    Video,
    Phone,
    MapPin,
    Loader2,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const SchedulingCalendar = ({ tenantId, token }) => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(null);
    const [dailySlots, setDailySlots] = useState([]);
    const [upcomingAppointments, setUpcomingAppointments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showAddSlot, setShowAddSlot] = useState(false);

    // Get calendar data
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const monthName = currentDate.toLocaleString('default', { month: 'long' });

    const firstDayOfMonth = new Date(year, month, 1);
    const lastDayOfMonth = new Date(year, month + 1, 0);
    const daysInMonth = lastDayOfMonth.getDate();
    const startingDay = firstDayOfMonth.getDay();

    const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // API helpers
    const getAuthHeaders = () => ({
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token || localStorage.getItem('token')}`,
    });

    // Fetch appointments for the current month
    const fetchAppointments = useCallback(async () => {
        const tid = tenantId || localStorage.getItem('tenantId');
        if (!tid) return;

        try {
            const startDate = new Date(year, month, 1).toISOString().split('T')[0];
            const endDate = new Date(year, month + 1, 0).toISOString().split('T')[0];

            const response = await fetch(
                `${API_BASE_URL}/api/v1/scheduling/appointments?tenant_id=${tid}&start_date=${startDate}&end_date=${endDate}`,
                { headers: getAuthHeaders() }
            );

            if (response.ok) {
                const data = await response.json();
                // Transform to UI format
                const formatted = data.map(apt => {
                    const aptDate = new Date(apt.scheduled_at);
                    const isToday = aptDate.toDateString() === new Date().toDateString();
                    const isTomorrow = aptDate.toDateString() === new Date(Date.now() + 86400000).toDateString();

                    let timeLabel = aptDate.toLocaleDateString();
                    if (isToday) timeLabel = 'Today';
                    if (isTomorrow) timeLabel = 'Tomorrow';

                    return {
                        id: apt.id,
                        clientName: apt.lead_name || `Lead #${apt.lead_id}`,
                        clientAvatar: null,
                        type: apt.type?.charAt(0).toUpperCase() + apt.type?.slice(1) || 'Viewing',
                        time: `${timeLabel}: ${aptDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
                        property: apt.notes || 'Property Appointment',
                        status: apt.status
                    };
                });
                setUpcomingAppointments(formatted.filter(a => a.status !== 'cancelled'));
            }
        } catch (error) {
            console.error('Error fetching appointments:', error);
        }
    }, [year, month, tenantId, token]);

    // Fetch available slots for a specific date
    const fetchSlotsForDate = useCallback(async (day) => {
        const tid = tenantId || localStorage.getItem('tenantId');
        if (!tid || !day) return;

        setLoading(true);
        try {
            const dateStr = new Date(year, month, day).toISOString().split('T')[0];
            const response = await fetch(
                `${API_BASE_URL}/api/v1/scheduling/available-slots?tenant_id=${tid}&date=${dateStr}`,
                { headers: getAuthHeaders() }
            );

            if (response.ok) {
                const data = await response.json();
                // Filter to only available slots
                const available = data.slots?.filter(s => s.available).map(s => s.time) || [];
                setDailySlots(available);
            } else {
                setDailySlots([]);
            }
        } catch (error) {
            console.error('Error fetching slots:', error);
            setDailySlots([]);
        } finally {
            setLoading(false);
        }
    }, [year, month, tenantId, token]);

    // Fetch data when month changes
    useEffect(() => {
        fetchAppointments();
    }, [fetchAppointments]);

    // Fetch slots when date is selected
    useEffect(() => {
        if (selectedDate) {
            fetchSlotsForDate(selectedDate);
        }
    }, [selectedDate, fetchSlotsForDate]);

    const navigateMonth = (direction) => {
        setCurrentDate(new Date(year, month + direction, 1));
        setSelectedDate(null);
        setDailySlots([]);
    };

    const isToday = (day) => {
        const today = new Date();
        return day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear();
    };

    const hasAppointment = (day) => {
        return upcomingAppointments.some(apt => {
            // Parse the time string to check the day
            const timeStr = apt.time;
            if (timeStr.startsWith('Today') && isToday(day)) return true;
            if (timeStr.startsWith('Tomorrow')) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                return day === tomorrow.getDate() && month === tomorrow.getMonth();
            }
            return false;
        });
    };

    // Adjust starting day for Monday-first calendar
    const adjustedStartingDay = startingDay === 0 ? 6 : startingDay - 1;

    // Generate calendar days
    const calendarDays = [];
    for (let i = 0; i < adjustedStartingDay; i++) {
        calendarDays.push(null);
    }
    for (let day = 1; day <= daysInMonth; day++) {
        calendarDays.push(day);
    }

    const handleDateClick = (day) => {
        if (day) {
            setSelectedDate(day);
        }
    };

    return (
        <div className="scheduling-panel h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Scheduling</h3>
            </div>

            {/* Month Navigation */}
            <div className="flex items-center justify-between mb-4 px-1">
                <button
                    onClick={() => navigateMonth(-1)}
                    className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-white transition-colors"
                >
                    <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm font-medium text-white">
                    {monthName} {year}
                </span>
                <button
                    onClick={() => navigateMonth(1)}
                    className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-white transition-colors"
                >
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>

            {/* Calendar Grid */}
            <div className="calendar-grid mb-4">
                {/* Week day headers */}
                {weekDays.map(day => (
                    <div key={day} className="calendar-header">
                        {day}
                    </div>
                ))}

                {/* Calendar days */}
                {calendarDays.map((day, index) => (
                    <div
                        key={index}
                        onClick={() => handleDateClick(day)}
                        className={`
              calendar-day
              ${!day ? 'invisible' : 'cursor-pointer'}
              ${isToday(day) ? 'calendar-day-today' : ''}
              ${selectedDate === day ? 'bg-gold-500/20 ring-1 ring-gold-500/50' : ''}
              ${hasAppointment(day) ? 'calendar-day-has-slots' : ''}
            `}
                    >
                        {day}
                    </div>
                ))}
            </div>

            {/* Available Slots Label */}
            <div className="flex items-center gap-2 mb-3 px-1">
                <span className="text-xs text-gray-400">
                    {selectedDate ? `Slots for ${month + 1}/${selectedDate}` : 'Available Slots'}
                </span>
                <div className="flex-1 h-px bg-white/5" />
                {loading && <Loader2 className="w-3 h-3 animate-spin text-gold-400" />}
            </div>

            {/* Time Slots */}
            <div className="grid grid-cols-4 gap-2 mb-6">
                {dailySlots.length > 0 ? (
                    dailySlots.map((time, index) => (
                        <div key={index} className="availability-slot justify-center">
                            <div className="slot-indicator hidden" />
                            <span className="text-xs text-gray-300">{time}</span>
                        </div>
                    ))
                ) : (
                    <div className="col-span-4 text-center text-xs text-gray-500 py-2">
                        {selectedDate ? 'No slots available' : 'Select a date'}
                    </div>
                )}
            </div>

            {/* Upcoming Section */}
            <div className="flex-1 overflow-y-auto">
                <div className="flex items-center gap-2 mb-3 px-1">
                    <span className="text-xs text-gray-400">Upcoming Appointments</span>
                    <div className="flex-1 h-px bg-white/5" />
                </div>
                <div className="space-y-3">
                    {upcomingAppointments.length > 0 ? (
                        upcomingAppointments.slice(0, 5).map((apt) => (
                            <div key={apt.id} className="upcoming-item">
                                <div className="flex items-center gap-3 flex-1">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-900 font-bold text-sm">
                                        {apt.clientName?.charAt(0) || '?'}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate">
                                            {apt.clientName}
                                        </p>
                                        <p className="text-xs text-gray-400">
                                            ({apt.type})
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-gold-400 font-medium">{apt.time.split(':')[0]}</p>
                                    <p className="text-xs text-gray-400">{apt.time.includes(':') ? apt.time.split(' ').slice(1).join(' ') : ''}</p>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center text-xs text-gray-500 py-4">
                            No upcoming appointments
                        </div>
                    )}
                </div>
            </div>

            {/* Set Availability Button */}
            <button
                onClick={() => setShowAddSlot(true)}
                className="w-full btn-gold mt-4 flex items-center justify-center gap-2"
            >
                <span>Set Availability</span>
                <Plus className="w-4 h-4" />
            </button>
        </div>
    );
};

export default SchedulingCalendar;

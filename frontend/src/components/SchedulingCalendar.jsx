/**
 * Artin Smart Realty - Scheduling Calendar Component
 * Monthly calendar with availability slots and upcoming appointments
 */

import React, { useState, useEffect } from 'react';
import {
    ChevronLeft,
    ChevronRight,
    Plus,
    Clock,
    User,
    Video,
    Phone,
    MapPin,
} from 'lucide-react';

const SchedulingCalendar = ({ tenantId, token }) => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(null);
    const [availableSlots, setAvailableSlots] = useState([]);
    const [upcomingAppointments, setUpcomingAppointments] = useState([]);
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

    // Sample data - replace with API calls
    useEffect(() => {
        // Fetch available slots and appointments
        setAvailableSlots([
            { date: new Date(year, month, 24), slots: ['10:00', '14:00', '16:00'] },
            { date: new Date(year, month, 25), slots: ['09:00', '11:00', '15:00'] },
            { date: new Date(year, month, 26), slots: ['10:00', '13:00'] },
            { date: new Date(year, month, 27), slots: ['11:00', '14:00', '16:00'] },
            { date: new Date(year, month, 28), slots: ['09:00', '10:00', '14:00'] },
        ]);

        setUpcomingAppointments([
            {
                id: 1,
                clientName: 'Michael Chen',
                clientAvatar: null,
                type: 'Viewing',
                time: 'Today: 4:00 PM',
                property: 'Downtown Penthouse',
            },
            {
                id: 2,
                clientName: 'Emma Davis',
                clientAvatar: null,
                type: 'Consultation',
                time: 'Tomorrow: 10:00 AM',
                property: 'Palm Jumeirah Villa',
            },
        ]);
    }, [year, month]);

    const navigateMonth = (direction) => {
        setCurrentDate(new Date(year, month + direction, 1));
    };

    const isToday = (day) => {
        const today = new Date();
        return day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear();
    };

    const hasSlots = (day) => {
        return availableSlots.some(slot =>
            slot.date.getDate() === day &&
            slot.date.getMonth() === month
        );
    };

    const getSlotsForDay = (day) => {
        const slot = availableSlots.find(s =>
            s.date.getDate() === day &&
            s.date.getMonth() === month
        );
        return slot?.slots || [];
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
                        onClick={() => day && setSelectedDate(day)}
                        className={`
              calendar-day
              ${!day ? 'invisible' : 'cursor-pointer'}
              ${isToday(day) ? 'calendar-day-today' : ''}
              ${selectedDate === day ? 'bg-gold-500/20 ring-1 ring-gold-500/50' : ''}
              ${hasSlots(day) ? 'calendar-day-has-slots' : ''}
            `}
                    >
                        {day}
                    </div>
                ))}
            </div>

            {/* Available Slots Label */}
            <div className="flex items-center gap-2 mb-3 px-1">
                <span className="text-xs text-gray-400">Available Slots</span>
                <div className="flex-1 h-px bg-white/5" />
            </div>

            {/* Time Slots */}
            <div className="grid grid-cols-4 gap-2 mb-6">
                {(selectedDate ? getSlotsForDay(selectedDate) : ['10:00', '11:00', '14:00', '16:00']).map((time, index) => (
                    <div key={index} className="availability-slot justify-center">
                        <div className="slot-indicator hidden" />
                        <span className="text-xs text-gray-300">{time}</span>
                    </div>
                ))}
            </div>

            {/* Upcoming Section */}
            <div className="flex-1 overflow-y-auto">
                <div className="space-y-3">
                    {upcomingAppointments.map((apt) => (
                        <div key={apt.id} className="upcoming-item">
                            <div className="flex items-center gap-3 flex-1">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-900 font-bold text-sm">
                                    {apt.clientName.charAt(0)}
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
                                <p className="text-xs text-gray-400">{apt.time.includes(':') ? apt.time.split(' ')[1] + ' ' + apt.time.split(' ')[2] : ''}</p>
                            </div>
                        </div>
                    ))}
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

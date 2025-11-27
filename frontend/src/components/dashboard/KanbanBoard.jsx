import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { getLeads, updateLeadStatus } from '../../api/client';
import { Bell, Phone, Mail, DollarSign, TrendingUp } from 'lucide-react';

/**
 * CRM Kanban Board - Heart of the System
 * Trello-style drag & drop lead management
 */

const COLUMNS = [
  { id: 'new', title: 'New Leads', color: 'bg-blue-500' },
  { id: 'qualified', title: 'Qualified', color: 'bg-yellow-500' },
  { id: 'negotiation', title: 'Negotiation', color: 'bg-orange-500' },
  { id: 'closed_won', title: 'Closed Won', color: 'bg-green-500' }
];

const getHotnessScore = (lead) => {
  let score = 0;
  
  // Budget factor
  if (lead.budget_max >= 2000000) score += 40;
  else if (lead.budget_max >= 1000000) score += 30;
  else if (lead.budget_max >= 500000) score += 20;
  else score += 10;
  
  // Response time factor
  const hoursSinceLastMessage = (Date.now() - new Date(lead.last_message_at)) / (1000 * 60 * 60);
  if (hoursSinceLastMessage < 1) score += 30;
  else if (hoursSinceLastMessage < 24) score += 20;
  else if (hoursSinceLastMessage < 72) score += 10;
  
  // Phone shared factor
  if (lead.phone_number) score += 30;
  
  return Math.min(100, score);
};

const HotnessIndicator = ({ score }) => {
  const getColor = () => {
    if (score >= 80) return 'text-red-500';
    if (score >= 60) return 'text-orange-500';
    if (score >= 40) return 'text-yellow-500';
    return 'text-gray-400';
  };
  
  return (
    <div className="flex items-center gap-1">
      <TrendingUp className={`w-4 h-4 ${getColor()}`} />
      <span className={`text-xs font-bold ${getColor()}`}>{score}°</span>
    </div>
  );
};

const LeadCard = ({ lead, index }) => {
  const hotnessScore = getHotnessScore(lead);
  
  return (
    <Draggable draggableId={lead.id.toString()} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`bg-white dark:bg-gray-800 rounded-lg p-4 mb-3 shadow-sm hover:shadow-md transition-shadow ${
            snapshot.isDragging ? 'shadow-lg ring-2 ring-blue-400' : ''
          }`}
        >
          {/* Header */}
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 dark:text-white">
                {lead.name || `Lead #${lead.id}`}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {lead.telegram_username || 'No username'}
              </p>
            </div>
            <HotnessIndicator score={hotnessScore} />
          </div>
          
          {/* Info */}
          <div className="space-y-1 mb-3">
            {lead.budget_max && (
              <div className="flex items-center gap-2 text-sm">
                <DollarSign className="w-4 h-4 text-green-600" />
                <span className="text-gray-700 dark:text-gray-300">
                  {lead.budget_max.toLocaleString()} AED
                </span>
              </div>
            )}
            
            {lead.phone_number && (
              <div className="flex items-center gap-2 text-sm">
                <Phone className="w-4 h-4 text-blue-600" />
                <span className="text-gray-700 dark:text-gray-300">
                  {lead.phone_number}
                </span>
              </div>
            )}
            
            {lead.property_type && (
              <div className="text-xs text-gray-600 dark:text-gray-400">
                {lead.property_type} • {lead.transaction_type || 'Buy'}
              </div>
            )}
          </div>
          
          {/* Tags */}
          <div className="flex gap-2">
            {lead.purpose === 'investment' && (
              <span className="px-2 py-1 text-xs bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
                💰 Investment
              </span>
            )}
            {lead.language && (
              <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                {lead.language.toUpperCase()}
              </span>
            )}
          </div>
        </div>
      )}
    </Draggable>
  );
};

const KanbanColumn = ({ column, leads }) => {
  return (
    <div className="flex-1 min-w-[300px]">
      {/* Column Header */}
      <div className={`${column.color} text-white rounded-t-lg px-4 py-3 flex justify-between items-center`}>
        <h3 className="font-semibold">{column.title}</h3>
        <span className="bg-white/20 px-2 py-1 rounded text-sm">
          {leads.length}
        </span>
      </div>
      
      {/* Droppable Area */}
      <Droppable droppableId={column.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`bg-gray-50 dark:bg-gray-900 p-3 rounded-b-lg min-h-[500px] ${
              snapshot.isDraggingOver ? 'bg-blue-50 dark:bg-blue-900/20' : ''
            }`}
          >
            {leads.map((lead, index) => (
              <LeadCard key={lead.id} lead={lead} index={index} />
            ))}
            {provided.placeholder}
            
            {leads.length === 0 && (
              <div className="text-center text-gray-400 dark:text-gray-600 py-8">
                Drop leads here
              </div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  );
};

export default function KanbanBoard() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadLeads();
  }, []);
  
  const loadLeads = async () => {
    try {
      const response = await getLeads();
      setLeads(response.data);
    } catch (error) {
      console.error('Failed to load leads:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const onDragEnd = async (result) => {
    const { source, destination, draggableId } = result;
    
    // Dropped outside
    if (!destination) return;
    
    // No change
    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }
    
    // Update lead status
    try {
      await updateLeadStatus(draggableId, destination.droppableId);
      
      // Update local state
      setLeads(prevLeads => 
        prevLeads.map(lead => 
          lead.id.toString() === draggableId 
            ? { ...lead, status: destination.droppableId }
            : lead
        )
      );
      
      // Show notification
      const audio = new Audio('/sounds/cha-ching.mp3');
      audio.play().catch(() => {});
      
    } catch (error) {
      console.error('Failed to update lead status:', error);
      alert('Failed to update lead status');
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">CRM Pipeline</h2>
        <p className="text-gray-600 dark:text-gray-400">Drag & drop leads to update their status</p>
      </div>
      
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map(column => (
            <KanbanColumn
              key={column.id}
              column={column}
              leads={leads.filter(lead => lead.status === column.id)}
            />
          ))}
        </div>
      </DragDropContext>
    </div>
  );
}

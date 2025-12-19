import { useState, useEffect } from 'react'
import { Layout } from '../components/Layout'
import LeadModal from '../components/LeadModal'
import DeleteConfirmModal from '../components/DeleteConfirmModal'
import Pagination from '../components/Pagination'
import LoadingSkeleton from '../components/LoadingSkeleton'
import EmptyState from '../components/EmptyState'
import { api, useAuth } from '../context/AuthContext'
import { toast } from '../utils/toast'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { 
  Plus, 
  Search, 
  Filter, 
  Download,
  Phone,
  Mail,
  Calendar,
  MapPin,
  Edit,
  Trash2,
  GripVertical
} from 'lucide-react'

const Leads = () => {
  const { user } = useAuth()
  const isViewer = user?.role === 'viewer'
  const isAdminOrSuperadmin = user?.role === 'admin' || user?.role === 'superadmin'
  
  const [leads, setLeads] = useState([])
  const [filteredLeads, setFilteredLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [selectedLead, setSelectedLead] = useState(null)
  const [modalMode, setModalMode] = useState('create')
  const [activeId, setActiveId] = useState(null)
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(50) // 50 leads per page
  const [totalPages, setTotalPages] = useState(1)
  const [totalFilteredItems, setTotalFilteredItems] = useState(0)

  // Drag & Drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  useEffect(() => {
    fetchLeads()
  }, [])

  useEffect(() => {
    filterLeads()
  }, [leads, searchQuery, filterStatus, currentPage])

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, filterStatus])

  const fetchLeads = async () => {
    try {
      const response = await api.get('/api/leads?limit=1000')
      setLeads(response.data.leads || [])
    } catch (error) {
      console.error('Failed to fetch leads:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterLeads = () => {
    let filtered = [...leads]

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(lead => lead.status === filterStatus)
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(lead =>
        lead.full_name?.toLowerCase().includes(query) ||
        lead.phone?.toLowerCase().includes(query) ||
        lead.email?.toLowerCase().includes(query) ||
        lead.product_interest?.toLowerCase().includes(query) ||
        lead.company_name?.toLowerCase().includes(query) ||
        lead.job_title?.toLowerCase().includes(query)
      )
    }

    // Calculate pagination
    setTotalFilteredItems(filtered.length)
    setTotalPages(Math.ceil(filtered.length / itemsPerPage))
    
    // Paginate results
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    const paginatedLeads = filtered.slice(startIndex, endIndex)
    
    setFilteredLeads(paginatedLeads)
  }

  const handleCreateLead = () => {
    setSelectedLead(null)
    setModalMode('create')
    setModalOpen(true)
  }

  const handleEditLead = (lead) => {
    setSelectedLead(lead)
    setModalMode('edit')
    setModalOpen(true)
  }

  const handleDeleteLead = (lead) => {
    setSelectedLead(lead)
    setDeleteModalOpen(true)
  }

  const handleSaveLead = async (data, leadId) => {
    try {
      if (modalMode === 'create') {
        await api.post('/api/leads', data)
        toast.success('Lead created successfully!')
      } else {
        await api.patch(`/api/leads/${leadId}`, data)
        toast.success('Lead updated successfully!')
      }
      fetchLeads()
      setModalOpen(false)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save lead')
      throw new Error(error.response?.data?.detail || 'Failed to save lead')
    }
  }

  const handleConfirmDelete = async () => {
    try {
      await api.delete(`/api/leads/${selectedLead.id}`)
      toast.success(`${selectedLead.full_name} deleted successfully`)
      fetchLeads()
      setDeleteModalOpen(false)
      setSelectedLead(null)
    } catch (error) {
      toast.error('Failed to delete lead. Please try again.')
      console.error('Failed to delete lead:', error)
    }
  }

  const handleDragStart = (event) => {
    setActiveId(event.active.id)
  }

  const handleDragEnd = async (event) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const activeLeadId = active.id
      const overColumnStatus = over.id
      const lead = leads.find(l => l.id === activeLeadId)

      // Update lead status
      try {
        await api.patch(`/api/leads/${activeLeadId}`, {
          status: overColumnStatus
        })
        toast.success(`${lead?.full_name || 'Lead'} moved successfully`)
        fetchLeads()
      } catch (error) {
        toast.error('Failed to update lead status')
        console.error('Failed to update lead status:', error)
      }
    }

    setActiveId(null)
  }

  const exportToExcel = () => {
    // Create CSV content
    const headers = ['Name', 'Email', 'Phone', 'Status', 'Property Type', 'Budget Min', 'Budget Max', 'Location', 'Created']
    const csvContent = [
      headers.join(','),
      ...filteredLeads.map(lead => [
        `"${lead.full_name || ''}"`,
        `"${lead.email || ''}"`,
        `"${lead.phone || ''}"`,
        `"${lead.status || ''}"`,
        `"${lead.property_type || ''}"`,
        lead.budget_min || '',
        lead.budget_max || '',
        `"${lead.preferred_location || ''}"`,
        `"${lead.created_at || ''}"`
      ].join(','))
    ].join('\n')

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `leads_export_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    
    toast.success(`Exported ${filteredLeads.length} leads to Excel`)
  }

  // Pipeline columns
  const columns = [
    { id: 'new', title: '🆕 Just Scanned', badge: 'red' },
    { id: 'qualified', title: '✨ Interested', badge: 'yellow' },
    { id: 'viewing_scheduled', title: '📞 Follow-up Scheduled', badge: 'green' },
    { id: 'closed_won', title: '🎉 Converted', badge: 'blue' }
  ]

  const getLeadsByStatus = (status) => {
    return filteredLeads.filter(lead => lead.status === status)
  }

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="flex items-center justify-between">
            <div className="h-10 bg-white/10 rounded w-48 animate-pulse"></div>
            <div className="h-10 bg-white/10 rounded w-32 animate-pulse"></div>
          </div>
          
          {/* Kanban Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="space-y-3">
                <div className="h-12 bg-white/10 rounded-xl animate-pulse"></div>
                <LoadingSkeleton type="card" count={3} className="space-y-3" />
              </div>
            ))}
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">📊 Booth Visitors</h1>
            <p className="text-white/50">{filteredLeads.length} visitors scanned today</p>
          </div>
          <button
            onClick={handleCreateLead}
            disabled={isViewer}
            className={`btn-gold flex items-center gap-2 ${isViewer ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={isViewer ? 'Viewers cannot create leads' : 'Create new lead'}
          >
            <Plus className="w-5 h-5" />
            <span>Add Visitor</span>
          </button>
        </div>

        {/* Toolbar */}
        <div className="glass-card rounded-xl p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search visitors by name, phone, email, company..."
                  className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 focus:ring-4 focus:ring-gold-500/10 transition-all"
                />
              </div>
            </div>

            {/* Filter */}
            <div className="flex gap-2">
              <div className="relative">
                <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40 pointer-events-none" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="pl-12 pr-8 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500/40 appearance-none cursor-pointer"
                >
                  <option value="all">All Visitors</option>
                  <option value="new">🆕 Just Scanned</option>
                  <option value="qualified">✨ Interested</option>
                  <option value="viewing_scheduled">📞 Follow-up Scheduled</option>
                  <option value="negotiation">💬 In Discussion</option>
                  <option value="closed_won">🎉 Converted to Customer</option>
                  <option value="closed_lost">❌ Not Interested</option>
                </select>
              </div>

              <button
                onClick={exportToExcel}
                className="px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white transition-all flex items-center gap-2"
              >
                <Download className="w-5 h-5" />
                <span className="hidden md:inline">Export</span>
              </button>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        {leads.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No visitors yet"
            description="Start scanning QR codes at your booth to collect visitor information and track leads."
            actionLabel="Create Manual Lead"
            onAction={!isViewer ? handleCreateLead : undefined}
          />
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {columns.map((column) => (
                <DroppableColumn
                  key={column.id}
                  column={column}
                  leads={getLeadsByStatus(column.id)}
                  onEdit={handleEditLead}
                  onDelete={handleDeleteLead}
                  isViewer={isViewer}
                />
              ))}
            </div>
            <DragOverlay>
              {activeId ? (
                <LeadCardDragOverlay
                  lead={leads.find(l => l.id === activeId)}
                />
              ) : null}
            </DragOverlay>
          </DndContext>
        )}

        {/* Pagination */}
        {leads.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            itemsPerPage={itemsPerPage}
            totalItems={totalFilteredItems}
          />
        )}

        {/* Modals */}
        <LeadModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          onSave={handleSaveLead}
          lead={selectedLead}
          mode={modalMode}
        />

        <DeleteConfirmModal
          isOpen={deleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={handleConfirmDelete}
          leadName={selectedLead?.full_name}
          isDeleting={false}
        />
      </div>
    </Layout>
  )
}

// Droppable Column Component
const DroppableColumn = ({ column, leads, onEdit, onDelete, isViewer = false }) => {
  const { setNodeRef } = useSortable({
    id: column.id,
    data: {
      type: 'column',
    },
  })

  const badgeClasses = {
    red: 'badge-red',
    yellow: 'badge-yellow',
    green: 'badge-green',
    blue: 'badge-blue'
  }

  return (
    <div
      ref={setNodeRef}
      className="glass-card rounded-2xl p-6 min-h-[600px] flex flex-col"
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <h3 className="font-semibold text-white">{column.title}</h3>
          <span className={badgeClasses[column.badge]}>{leads.length}</span>
        </div>
      </div>

      {/* Lead Cards */}
      <SortableContext
        items={leads.map(l => l.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-4 flex-1 overflow-y-auto">
          {leads.length > 0 ? (
            leads.map((lead) => (
              <DraggableLeadCard
                key={lead.id}
                lead={lead}
                onEdit={onEdit}
                onDelete={onDelete}
                isViewer={isViewer}
              />
            ))
          ) : (
            <div className="flex items-center justify-center h-40 text-white/30 text-sm">
              No leads in this stage
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

// Draggable Lead Card
const DraggableLeadCard = ({ lead, onEdit, onDelete, isViewer = false }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: lead.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  // Temperature Badge Helper
  const getTemperatureBadge = (temperature) => {
    const badges = {
      burning: { emoji: '🔥', color: 'bg-red-500/20 text-red-400 border-red-500/30', label: 'BURNING' },
      hot: { emoji: '🌶️', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', label: 'HOT' },
      warm: { emoji: '☀️', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', label: 'WARM' },
      cold: { emoji: '❄️', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'COLD' },
    }
    return badges[temperature] || badges.cold
  }

  const tempBadge = getTemperatureBadge(lead.temperature)

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 hover:border-gold-500/30 transition-all group"
    >
      {/* Drag Handle - disabled for viewers */}
      <div className="flex items-start gap-3">
        {!isViewer && (
          <button
            {...attributes}
            {...listeners}
            className="p-1 hover:bg-white/10 rounded cursor-grab active:cursor-grabbing"
          >
            <GripVertical className="w-4 h-4 text-white/40" />
          </button>
        )}

        <div className="flex-1">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="font-semibold text-white group-hover:text-gold-500 transition-colors">
                  {lead.full_name}
                </h4>
                {/* Lead Score Badge */}
                {lead.lead_score !== undefined && lead.lead_score > 0 && (
                  <span className="text-xs font-bold text-gold-500 bg-gold-500/10 px-2 py-0.5 rounded">
                    {lead.lead_score}
                  </span>
                )}
              </div>
              <p className="text-sm text-white/50">{lead.product_interest || 'Booth Visitor'}</p>
            </div>
            
            {/* Temperature Badge */}
            {lead.temperature && (
              <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-xs font-bold ${tempBadge.color}`}>
                <span>{tempBadge.emoji}</span>
                <span>{tempBadge.label}</span>
              </div>
            )}
          </div>

          <div className="space-y-2 text-xs text-white/60 mb-3">
            {lead.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-3 h-3 text-gold-500" />
                <span>{lead.phone}</span>
              </div>
            )}
            {lead.email && (
              <div className="flex items-center gap-2">
                <Mail className="w-3 h-3 text-gold-500" />
                <span>{lead.email}</span>
              </div>
            )}
            
            {/* Engagement Stats */}
            {lead.total_interactions > 0 && (
              <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                {lead.qr_scan_count > 0 && (
                  <span className="text-white/40">📱 {lead.qr_scan_count} scans</span>
                )}
                {lead.catalog_views > 0 && (
                  <span className="text-white/40">📄 {lead.catalog_views} views</span>
                )}
                {lead.messages_count > 0 && (
                  <span className="text-white/40">💬 {lead.messages_count} msgs</span>
                )}
              </div>
            )}
          </div>

          {lead.budget_max && (
            <div className="mb-3 pt-3 border-t border-white/5">
              <p className="text-sm font-bold text-gold-500">
                Order Value: ${(lead.budget_max / 1000).toFixed(0)}K
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => onEdit(lead)}
              disabled={isViewer}
              className={`flex-1 px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${isViewer ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={isViewer ? 'Viewers cannot edit leads' : 'Edit lead'}
            >
              <Edit className="w-3 h-3" />
              Edit
            </button>
            <button
              onClick={() => onDelete(lead)}
              disabled={isViewer}
              className={`flex-1 px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1 ${isViewer ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={isViewer ? 'Viewers cannot delete leads' : 'Delete lead'}
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Drag Overlay Component
const LeadCardDragOverlay = ({ lead }) => {
  if (!lead) return null

  return (
    <div className="bg-white/10 border-2 border-gold-500 rounded-xl p-4 shadow-2xl backdrop-blur-xl w-72">
      <h4 className="font-semibold text-white">{lead.full_name}</h4>
      <p className="text-sm text-white/70">{lead.property_type || 'Property Interest'}</p>
    </div>
  )
}

export default Leads

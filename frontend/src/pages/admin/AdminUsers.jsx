import { useState } from 'react'
import DataTable from '../../components/admin/DataTable'
import StatusBadge from '../../components/admin/StatusBadge'
import { mockUsers } from '../../data/mockAdmin'

export default function AdminUsers() {
  const [search, setSearch] = useState('')

  const filtered = mockUsers.filter(u =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  const columns = [
    { key: 'name',           label: 'Name' },
    { key: 'email',          label: 'Email' },
    { key: 'role',           label: 'Role',        render: (v) => <StatusBadge status={v} /> },
    { key: 'status',         label: 'Status',      render: (v) => <StatusBadge status={v} /> },
    { key: 'lastActive',     label: 'Last Active' },
    { key: 'signalsViewed',  label: 'Signals',     render: (v) => <span className="monospaced">{v}</span> },
    { key: 'actions',        label: '',             sortable: false, render: (_, row) => (
      <div className="flex gap-2">
        <button className="text-[9px] uppercase tracking-[0.2em] text-gray-600 hover:text-red-500 transition-colors">
          Edit
        </button>
        <button className="text-[9px] uppercase tracking-[0.2em] text-gray-600 hover:text-red-500 transition-colors">
          {row.status === 'suspended' ? 'Restore' : 'Suspend'}
        </button>
      </div>
    )},
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-sm uppercase tracking-[0.5em] font-light">User Management</h1>
          <div className="h-px w-8 bg-red-600 mt-2" />
        </div>
        <div className="flex gap-3 items-center">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search users..."
            className="bg-transparent border border-white/10 rounded px-3 py-1.5 text-[11px] tracking-wide w-56 focus:outline-none focus:border-red-600/50 transition-colors"
          />
          <div className="text-[9px] text-gray-600 uppercase tracking-[0.2em]">
            {filtered.length} users
          </div>
        </div>
      </div>

      <DataTable columns={columns} data={filtered} />
    </div>
  )
}

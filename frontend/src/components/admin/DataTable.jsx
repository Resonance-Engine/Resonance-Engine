import { useState } from 'react'

export default function DataTable({ columns, data, onRowClick, expandable }) {
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const [expandedRow, setExpandedRow] = useState(null)

  const handleSort = (key) => {
    if (sortCol === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(key)
      setSortDir('asc')
    }
  }

  const sorted = [...data].sort((a, b) => {
    if (!sortCol) return 0
    const av = a[sortCol], bv = b[sortCol]
    if (av == null) return 1
    if (bv == null) return -1
    const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv))
    return sortDir === 'asc' ? cmp : -cmp
  })

  return (
    <div className="glass-panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-white/5">
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                  className={`px-4 py-3 text-[9px] uppercase tracking-[0.3em] text-gray-500 font-normal whitespace-nowrap ${col.sortable !== false ? 'cursor-pointer hover:text-red-500 transition-colors select-none' : ''}`}
                >
                  {col.label}
                  {sortCol === col.key && (
                    <span className="ml-1 text-red-500">{sortDir === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <>
                <tr
                  key={row.id || i}
                  onClick={() => {
                    if (expandable) setExpandedRow(expandedRow === i ? null : i)
                    onRowClick?.(row)
                  }}
                  className={`border-b border-white/[0.03] transition-colors ${(expandable || onRowClick) ? 'cursor-pointer hover:bg-white/[0.02]' : ''} ${expandedRow === i ? 'bg-white/[0.02]' : ''}`}
                >
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3 text-[11px] font-light tracking-wide whitespace-nowrap">
                      {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
                {expandable && expandedRow === i && (
                  <tr key={`${row.id || i}-expand`} className="bg-white/[0.01]">
                    <td colSpan={columns.length} className="px-4 py-4">
                      {expandable(row)}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import type { ReactNode } from "react";

export interface DataColumn<Row> {
  id: string;
  header: string;
  render: (row: Row) => ReactNode;
  align?: "start" | "end";
}

interface DataTableProps<Row> {
  caption: string;
  columns: readonly DataColumn<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row) => string;
  emptyMessage?: string;
}

export function DataTable<Row>({
  caption,
  columns,
  rows,
  rowKey,
  emptyMessage = "No evidence available.",
}: DataTableProps<Row>) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th data-align={column.align} key={column.id} scope="col">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((column) => (
                  <td data-align={column.align} key={column.id}>
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td className="data-table__empty" colSpan={columns.length}>
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

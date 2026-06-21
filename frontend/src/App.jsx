import { useEffect, useState } from 'react';

const API = '/api';
const CATEGORIES = ['Food', 'Transport', 'Bills', 'Entertainment', 'Shopping', 'Health', 'Other'];

export default function App() {
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [form, setForm] = useState({
    amount: '',
    category: 'Food',
    description: '',
    spent_on: new Date().toISOString().slice(0, 10),
  });
  const [error, setError] = useState('');

  async function load() {
    try {
      const [e, s] = await Promise.all([
        fetch(`${API}/expenses`).then(r => r.json()),
        fetch(`${API}/summary?days=30`).then(r => r.json()),
      ]);
      setExpenses(e);
      setSummary(s);
    } catch (err) {
      setError('Failed to load data');
    }
  }

  useEffect(() => { load(); }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!form.amount || Number(form.amount) <= 0) {
      setError('Amount must be greater than 0');
      return;
    }
    const res = await fetch(`${API}/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: form.amount,
        category: form.category,
        description: form.description || null,
        spent_on: form.spent_on,
      }),
    });
    if (!res.ok) {
      setError('Failed to save expense');
      return;
    }
    setForm({ ...form, amount: '', description: '' });
    load();
  }

  async function handleDelete(id) {
    await fetch(`${API}/expenses/${id}`, { method: 'DELETE' });
    load();
  }

  return (
    <div className="container">
      <h1>💸 Daily Expense Logger</h1>

      <div className="card">
        <h2>Add expense</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <input
              type="number"
              step="0.01"
              placeholder="Amount"
              value={form.amount}
              onChange={e => setForm({ ...form, amount: e.target.value })}
            />
            <select
              value={form.category}
              onChange={e => setForm({ ...form, category: e.target.value })}
            >
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input
              type="text"
              placeholder="Description (optional)"
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
            />
            <input
              type="date"
              value={form.spent_on}
              onChange={e => setForm({ ...form, spent_on: e.target.value })}
            />
            <button type="submit">Add</button>
          </div>
          {error && <div className="error">{error}</div>}
        </form>
      </div>

      <div className="card">
        <h2>Last 30 days</h2>
        {summary && summary.by_category.length === 0 && (
          <p className="muted">No expenses yet — add one above.</p>
        )}
        {summary && summary.by_category.map(c => (
          <div key={c.category} className="summary-row">
            <span>{c.category} <span className="muted">({c.count})</span></span>
            <span className="amount">{Number(c.total).toFixed(2)}</span>
          </div>
        ))}
        {summary && summary.by_category.length > 0 && (
          <div className="summary-total">
            <span>Total</span>
            <span>{Number(summary.total).toFixed(2)}</span>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Recent expenses</h2>
        {expenses.length === 0 ? (
          <p className="muted">Nothing logged yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {expenses.map(x => (
                <tr key={x.id}>
                  <td>{x.spent_on}</td>
                  <td>{x.category}</td>
                  <td>{x.description || <span className="muted">—</span>}</td>
                  <td className="amount" style={{ textAlign: 'right' }}>{Number(x.amount).toFixed(2)}</td>
                  <td>
                    <button className="danger" onClick={() => handleDelete(x.id)}>×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

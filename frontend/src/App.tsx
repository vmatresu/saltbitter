import { useState, useEffect } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')

  useEffect(() => {
    // Check backend health
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('offline'))
  }, [])

  return (
    <div style={{
      fontFamily: 'system-ui, sans-serif',
      maxWidth: '800px',
      margin: '0 auto',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <h1>🌊 SaltBitter Dating Platform</h1>
      <p style={{ fontSize: '1.2rem', color: '#666' }}>
        Psychology-Informed Ethical Dating
      </p>

      <div style={{
        marginTop: '3rem',
        padding: '2rem',
        background: '#f5f5f5',
        borderRadius: '8px'
      }}>
        <h2>✅ Development Environment Active</h2>
        <p>
          <strong>Backend API Status:</strong>{' '}
          <span style={{
            color: apiStatus === 'healthy' ? 'green' : 'red',
            fontWeight: 'bold'
          }}>
            {apiStatus}
          </span>
        </p>

        <div style={{ marginTop: '2rem', textAlign: 'left' }}>
          <h3>🔗 Quick Links</h3>
          <ul>
            <li><a href="http://localhost:8000/docs" target="_blank">Backend API Docs (Swagger)</a></li>
            <li><a href="http://localhost:8025" target="_blank">Mailhog Email Testing</a></li>
            <li><a href="http://localhost:9001" target="_blank">MinIO Console (S3)</a></li>
            <li><a href="http://localhost:8080" target="_blank">Adminer (Database UI)</a></li>
          </ul>
        </div>

        <div style={{ marginTop: '2rem', textAlign: 'left' }}>
          <h3>📚 Documentation</h3>
          <ul>
            <li>Development Guide: <code>docs/DEVELOPMENT.md</code></li>
            <li>Architecture: <code>.agents/projects/dating-platform/architecture.toon</code></li>
            <li>Project Spec: <code>.agents/projects/dating-platform.toon</code></li>
          </ul>
        </div>
      </div>

      <div style={{ marginTop: '2rem', color: '#888', fontSize: '0.9rem' }}>
        <p>This is a development bootstrap page. Real implementation coming soon!</p>
      </div>
    </div>
  )
}

export default App

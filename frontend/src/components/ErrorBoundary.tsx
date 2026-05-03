import { Component, ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: '2rem', fontFamily: 'monospace' }}>
          <h2>Something went wrong</h2>
          <pre style={{ color: '#c0392b' }}>{this.state.error.message}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

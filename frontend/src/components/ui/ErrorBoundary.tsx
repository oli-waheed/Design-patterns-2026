import { Component, type ErrorInfo, type ReactNode } from 'react'

type ErrorBoundaryProps = {
  /** Shown in the fallback, e.g. the section title. */
  name: string
  children: ReactNode
}

type ErrorBoundaryState = {
  error: Error | null
}

/**
 * Catches a crash inside one dashboard section so the rest of the
 * dashboard keeps working, and offers a retry.
 */
export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`${this.props.name} crashed`, error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="alert-error mt-4" role="alert">
          <p className="font-semibold">
            {this.props.name} could not be displayed.
          </p>
          <p className="mt-1">{this.state.error.message}</p>
          <button
            type="button"
            className="btn btn-secondary btn-sm mt-3"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

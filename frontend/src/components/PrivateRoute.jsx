import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function PrivateRoute({ children }) {
    const { isAuthed } = useAuth()
    const location = useLocation()

    if (!isAuthed) {
        return <Navigate to="/login" state={{ from: location }} replace />
    }
    return children
}

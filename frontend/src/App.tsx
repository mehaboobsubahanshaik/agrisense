import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Chat from './pages/Chat'
import CropChoice from './pages/CropChoice'
import Dashboard from './pages/Dashboard'
import Disease from './pages/Disease'
import Landing from './pages/Landing'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Notifications from './pages/Notifications'
import Schemes from './pages/Schemes'
import Settings from './pages/Settings'
import Soil from './pages/Soil'
import VerifyOtp from './pages/VerifyOtp'
import Weather from './pages/Weather'
import YieldPage from './pages/Yield'
import { useAuth } from './store/auth'

function Protected({ children }: { children: React.ReactNode }) {
  const access = useAuth((s) => s.access)
  return access ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/verify" element={<VerifyOtp />} />
      <Route path="/app" element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<Chat />} />
        <Route path="scan" element={<Disease />} />
        <Route path="soil" element={<Soil />} />
        <Route path="weather" element={<Weather />} />
        <Route path="crops" element={<CropChoice />} />
        <Route path="yield" element={<YieldPage />} />
        <Route path="schemes" element={<Schemes />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

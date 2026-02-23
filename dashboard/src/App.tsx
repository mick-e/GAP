import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated } from './api/client'
import Layout from './components/Layout'
import PageLoader from './components/PageLoader'

const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Repos = lazy(() => import('./pages/Repos'))
const RepoDetail = lazy(() => import('./pages/RepoDetail'))
const Contributors = lazy(() => import('./pages/Contributors'))
const ContributorDetail = lazy(() => import('./pages/ContributorDetail'))
const Trends = lazy(() => import('./pages/Trends'))
const Teams = lazy(() => import('./pages/Teams'))
const Reports = lazy(() => import('./pages/Reports'))
const Settings = lazy(() => import('./pages/Settings'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="repos" element={<Repos />} />
          <Route path="repos/:name" element={<RepoDetail />} />
          <Route path="contributors" element={<Contributors />} />
          <Route path="contributors/:username" element={<ContributorDetail />} />
          <Route path="trends" element={<Trends />} />
          <Route path="teams" element={<Teams />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

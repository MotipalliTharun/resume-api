import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './Layout';
import { TailorPage } from './pages/TailorPage';
import { CoverLetterPage } from './pages/CoverLetterPage';
import { TrackerPage } from './pages/TrackerPage';
import { AnalysisPage } from './pages/AnalysisPage';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<TailorPage />} />
          <Route path="tracker" element={<TrackerPage />} />
          <Route path="cover-letter" element={<CoverLetterPage />} />
          <Route path="analysis/:id" element={<AnalysisPage />} />
          <Route path="analysis" element={<Navigate to="/tracker" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

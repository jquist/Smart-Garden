import { Route, Routes } from 'react-router-dom';
import MainLayout from './components/mainLayout';
import Plant from './pages/Plant';
import Home from './pages/Home';
import NotFound from './pages/NotFound';
import Database from './pages/database';
import Scheduler from './pages/Scheduler'
import FreeMoveCanvas from './pages/canvas';
function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        <Route path="/plant/:id" element={<Plant />} />
        <Route path="/database" element={<Database />} />
        <Route path="/canvas" element={<FreeMoveCanvas />} />
        <Route path="/scheduler" element={<Scheduler />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;

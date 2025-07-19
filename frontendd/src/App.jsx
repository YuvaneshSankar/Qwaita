import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Signup from './components/Signup'
import JoinQueue from './components/JoinQueue'

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Signup />} />
        <Route path="/join" element={<JoinQueue />} />
      </Routes>
    </Router>
  )
}

export default App

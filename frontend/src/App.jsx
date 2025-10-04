import React from "react";
import { Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Home from "./components/Home";
import AuthFilter from "./filter/AuthFilter";
import CaseDetails from "./components/CaseDetails";
import Navbar from "./components/Navbar";
import QueryLogs from "./components/QueryLogs";
import Register from "./components/Register";

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <AuthFilter>
              <Home />
            </AuthFilter>
          }
        />
        <Route
          path="/register"
          element={
            <Register/>
          }
        />
        <Route 
          path="/query-logs"
          element={
            <AuthFilter>
              <QueryLogs/>
            </AuthFilter>
          }
        />
        <Route
          path="/caseDetails"
          element={
            <AuthFilter>
              <CaseDetails />
            </AuthFilter>
          }
        />
      </Routes>
    </>
  );
}

export default App;

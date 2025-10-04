import React from "react";
import { Navigate } from "react-router-dom";

const AuthFilter = ({ children }) => {
  const token = localStorage.getItem("authToken");

  // if no token → redirect to login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // if token exists → allow access
  return children;
};

export default AuthFilter;

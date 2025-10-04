import React, { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import useLogout from "./Logout";

function Navbar() {
  const logout = useLogout();
  const navigate = useNavigate();
  const token = localStorage.getItem("authToken");
  const [isClosing, setIsClosing] = useState(false);

  const handleCloseDriver = async () => {
    const confirmClose = window.confirm("Are you sure you want to close the driver?");
    if (!confirmClose) return;

    setIsClosing(true);
    try {
      const response = await axios.get("http://127.0.0.1:8000/api/close_driver/", {
        headers: {
          Authorization: `Token ${token}`,
        },
      });
      alert(response.data.status);
    } catch (error) {
      console.error("Error closing driver:", error);
      alert("Failed to close driver. Please try again.");
    } finally {
      setIsClosing(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">Court Case Search</Link>
        <ul className="navbar-nav me-auto">
          {token && (
            <li className="nav-item">
              <Link className="nav-link" to="/query-logs">
                Query Logs
              </Link>
            </li>
          )}
        </ul>
        <div className="d-flex">
          {token && (
            <button
              className="btn btn-outline-warning me-2"
              onClick={handleCloseDriver}
              disabled={isClosing}
            >
              {isClosing ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                  Closing...
                </>
              ) : (
                "Close Driver"
              )}
            </button>
          )}
          {token ? (
            <button className="btn btn-outline-danger" onClick={handleLogout}>
              Logout
            </button>
          ) : (
            <Link className="btn btn-outline-primary" to="/login">
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

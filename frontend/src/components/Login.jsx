import React, { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    try {
      const response = await axios.post("http://127.0.0.1:8000/api/login/", {
        username,
        password,
      });

      if (response.data.status === "success") {
        setSuccess("Login successful!");
        // ✅ Save token to localStorage for future requests
        localStorage.setItem("authToken", response.data.token);
        localStorage.setItem("username", response.data.username);
        navigate("/");

        console.log("User logged in:", response.data);
      }
    } catch (err) {
      if (err.response) {
        setError(err.response.data.error || "Login failed.");
      } else {
        setError("Server not reachable.");
      }
    }
  };

  return (
    <div
      className="d-flex justify-content-center align-items-center vh-100"
      style={{ background: "linear-gradient(to right, #6a11cb, #2575fc)" }}
    >
      <div
        className="card p-4 shadow-lg"
        style={{ borderRadius: "15px", maxWidth: "100%", width: "100%" }}
      >
        <h3 className="text-center mb-4">Login</h3>
        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-control"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <p>u don't have an account ? <Link to="/register">Register</Link></p>

          <button type="submit" className="btn btn-primary w-100">
            Login
          </button>
        </form>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import LogCard from "./LogCard";
import LogDetail from "./LogDetail";

function QueryLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  const navigate = useNavigate();
  const token = localStorage.getItem("authToken");

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/logs/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });
        setLogs(response.data.logs);
      } catch (err) {
        if (err.response && err.response.status === 401) {
          localStorage.removeItem("authToken");
          navigate("/login");
        } else {
          setError("Failed to fetch logs. Please try again.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (!token) {
      navigate("/login");
    } else {
      fetchLogs();
    }
  }, [token, navigate]);

  if (loading) {
    return <div className="text-center mt-5">Loading...</div>;
  }

  if (error) {
    return <div className="alert alert-danger mt-3">{error}</div>;
  }

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Your Query Logs</h2>
      <div className="row">
        <div className="col-md-4">
          <div
            className="d-flex flex-column"
            style={{ maxHeight: "70vh", overflowY: "auto" }}
          >
            {logs.length === 0 ? (
              <div className="alert alert-info">No query logs found.</div>
            ) : (
              logs.map((log) => (
                <LogCard
                  key={log.id}
                  log={log}
                  onClick={setSelectedLog}
                />
              ))
            )}
          </div>
        </div>
        <div className="col-md-8">
          <LogDetail log={selectedLog} />
        </div>
      </div>
    </div>
  );
}

export default QueryLogs;

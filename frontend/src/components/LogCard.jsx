import React from "react";

function LogCard({ log, onClick }) {
  return (
    <div
      className="card mb-2"
      style={{ cursor: "pointer" }}
      onClick={() => onClick(log)}
    >
      <div className="card-body">
        <h6 className="card-title">{log.endpoint}</h6>
        <p className="card-text">
          <small className="text-muted">
            {new Date(log.request_timestamp).toLocaleString()}
          </small>
        </p>
        <p className="card-text">
          Status: {log.status_code}
        </p>
      </div>
    </div>
  );
}

export default LogCard;

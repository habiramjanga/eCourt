import React from "react";

function LogDetail({ log }) {
  if (!log) return null;

  return (
    <div className="card mt-3">
      <div className="card-body">
        <h5 className="card-title">Log Details</h5>
        <div className="mb-3">
          <h6>Endpoint: {log.endpoint}</h6>
          <p>
            <strong>Status Code:</strong> {log.status_code}
          </p>
          <p>
            <strong>Timestamp:</strong>{" "}
            {new Date(log.request_timestamp).toLocaleString()}
          </p>
          <p>
            <strong>IP Address:</strong> {log.ip_address}
          </p>
          <p>
            <strong>User:</strong> {log.username || "Unknown"}
          </p>
        </div>
        <div className="mb-3">
          <h6>Request Data:</h6>
          <pre className="bg-light p-3 rounded">
            {JSON.stringify(log.request_data, null, 2)}
          </pre>
        </div>
        <div className="mb-3">
          <h6>Response Data:</h6>
          {log.response_data.is_next_hearing_tomorrow && (
            <div className="alert alert-warning">
              Tomorrow is your hearing date!
            </div>
          )}
          <div dangerouslySetInnerHTML={{ __html: log.response_data.html_content }} />
          {log.response_data.pdf_url && (
            <div className="mt-3">
              <a
                href={log.response_data.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-info"
              >
                Download PDF
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default LogDetail;

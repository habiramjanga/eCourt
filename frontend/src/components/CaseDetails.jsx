import React from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";

function CaseResult() {
  const location = useLocation();
  const response = location.state?.response;
  const token = localStorage.getItem("authToken");

  if (!response) return <div>No such case available.</div>;

  const handleDownloadPDF = async () => {
    try {
      // Fetch the PDF file
      const res = await axios.post(
        "http://127.0.0.1:8000/api/download_pdf/",
        {},
        {
          headers: { Authorization: `Token ${token}` },
          responseType: "blob", // Important: Set responseType to 'blob' for binary data
        }
      );

      // Create a URL for the PDF blob
      const url = window.URL.createObjectURL(new Blob([res.data]));

      // Create a temporary anchor element to trigger the download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "order.pdf");
      document.body.appendChild(link);
      link.click();

      // Clean up
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading PDF:", error);
      alert("Failed to download PDF. Please try again.");
    }
  };

  return (
    <div className="mt-4">
      <h5>Case Details</h5>
      {/* Display "Tomorrow is your hearing date!" if is_next_hearing_tomorrow is true */}
      {response.is_next_hearing_tomorrow && (
        <div className="alert alert-warning">
          Tomorrow is your hearing date!
        </div>
      )}
      {/* Display HTML content */}
      {response.html_content=="" ? (<p>No case with the given details</p>):(
        <div dangerouslySetInnerHTML={{ __html: response.html_content }} />
      )}
      {/* Display PDF URL if available */}
      {response.pdf_url && (
        <div className="mt-3">
          <button
            onClick={handleDownloadPDF}
            className="btn btn-info"
          >
            Download PDF
          </button>
        </div>
      )}
    </div>
  );
}

export default CaseResult;

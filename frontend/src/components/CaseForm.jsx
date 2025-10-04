import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function CaseForm({ caseTypes, captcha, court }) {
   const [selectedCaseType, setSelectedCaseType] = useState("");
  const [caseNumber, setCaseNumber] = useState("");
  const [caseYear, setCaseYear] = useState("");
  const [captchaText, setCaptchaText] = useState("");
  const [loadingCaptcha, setLoadingCaptcha] = useState(false);
  const token = localStorage.getItem("authToken");
  const [response,setResponse] = useState([])
  const navigate = useNavigate();

  // Initialize captcha_img state with the prop value
  const [captchaImg, setCaptchaImg] = useState(captcha);

  // Update captcha_img when the captcha prop changes
  useEffect(() => {
    setCaptchaImg(captcha);
  }, [court]);

  // Function to refresh CAPTCHA
  const handleRefreshCaptcha = async () => {
    if (!court) return;

    setLoadingCaptcha(true);
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/set_court_and_get_case_types/",
        { court },
        { headers: { Authorization: `Token ${token}` } }
      );

      if (res.data.captcha_image) {
        setCaptchaImg(res.data.captcha_image);
      } else {
        console.error("No captcha image in response:", res.data);
      }
    } catch (err) {
      console.error("Error refreshing CAPTCHA:", err);
      if (err.response) {
        console.error("Response data:", err.response.data);
        console.error("Response status:", err.response.status);
      }
    } finally {
      setLoadingCaptcha(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/api/post_case_inputs/",
        {
          case_type: selectedCaseType,
          case_number: caseNumber,
          case_year: caseYear,
          captcha_text: captchaText,
        },
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
      setResponse(res.data);
      console.log("Response:", res.data);
      navigate("/caseDetails", { state: { response: res.data } });
    } catch (error) {
      console.error(error);
      setResponse({ error: "Something went wrong" });
    }
  };

  return (
    <div className="container mt-4">
      <h4 className="mb-3">Enter Case Details</h4>
      <form onSubmit={handleSubmit} className="p-3 border rounded bg-light shadow-sm">
        {/* Case Type Dropdown */}
        <div className="mb-3">
          <label className="form-label">Case Type</label>
          <select
            className="form-select"
            value={selectedCaseType}
            onChange={(e) => setSelectedCaseType(e.target.value)}
            required
          >
            <option value="">-- Choose Case Type --</option>
            {caseTypes.map((ct, i) => (
              <option key={i} value={ct}>
                {ct}
              </option>
            ))}
          </select>
        </div>

        {/* Case Number */}
        <div className="mb-3">
          <label className="form-label">Case Number</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter Case Number"
            value={caseNumber}
            onChange={(e) => setCaseNumber(e.target.value)}
            required
          />
        </div>

        {/* Case Year */}
        <div className="mb-3">
          <label className="form-label">Case Year</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter Case Year"
            value={caseYear}
            onChange={(e) => setCaseYear(e.target.value)}
            required
          />
        </div>

        {/* Captcha */}
      <div className="mb-3">
        <label className="form-label">Captcha</label>
        <div className="d-flex align-items-center">
          {captchaImg ? (
            <img
              src={captchaImg}
              alt="captcha"
              className="me-3 border rounded"
              style={{ height: "40px" }}
            />
          ) : (
            <div className="me-3 border rounded p-2 bg-light" style={{ height: "40px", width: "120px" }}>
              {loadingCaptcha ? "Loading..." : "No CAPTCHA"}
            </div>
          )}
          <input
            type="text"
            className="form-control"
            placeholder="Enter Captcha"
            value={captchaText}
            onChange={(e) => setCaptchaText(e.target.value)}
            required
            disabled={!captchaImg}
          />
          {/* Refresh Captcha Button */}
          <button
            type="button"
            className="btn btn-outline-secondary ms-2"
            onClick={handleRefreshCaptcha}
            disabled={!court || loadingCaptcha}
          >
            {loadingCaptcha ? (
              <>
                <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                Refreshing...
              </>
            ) : (
              "✱ Refresh"
            )}
          </button>
        </div>
      </div>

        {/* Submit Button */}
        <button type="submit" onClick={handleSubmit} className="btn btn-primary w-100" disabled={!captcha}>
          Submit
        </button>
      </form>
    </div>
  );
}

export default CaseForm;

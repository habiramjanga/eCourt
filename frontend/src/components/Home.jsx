import React, { useEffect, useState } from "react";
import axios from "axios";
import CaseForm from "./CaseForm";

function Home() {
  const [states, setStates] = useState([]);
  const [districts, setDistricts] = useState([]);
  const [courts, setCourts] = useState([]);
  const [caseTypes, setCaseTypes] = useState([]);
  const [captcha, setCaptcha] = useState(null);
  const [selectedState, setSelectedState] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedCourt, setSelectedCourt] = useState("");
  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingDistricts, setLoadingDistricts] = useState(false);
  const [loadingCourts, setLoadingCourts] = useState(false);
  const [loadingCaseTypes, setLoadingCaseTypes] = useState(false);
  const token = localStorage.getItem("authToken"); // token from login

  // ✅ Step 1: Fetch states on load
  useEffect(() => {
    const fetchStates = async () => {
      setLoadingStates(true);
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/", {
          headers: { Authorization: `Token ${token}` },
        });
        setStates(res.data.states || []);
        console.log("States fetched:", res.data.states);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingStates(false);
      }
    };

    if (token) {
      fetchStates();
    }
  }, [token]);

  // ✅ Step 2: Handle state selection → fetch districts
  const handleStateSelect = async (e) => {
    const state = e.target.value;
    setSelectedState(state);
    setSelectedDistrict("");
    setSelectedCourt("");
    setDistricts([]);
    setCourts([]);
    setCaseTypes([]);
    setCaptcha(null);

    if (state) {
      setLoadingDistricts(true);
      try {
        const res = await axios.post(
          "http://127.0.0.1:8000/api/",
          { state },
          { headers: { Authorization: `Token ${token}` } }
        );
        setDistricts(res.data.districts || []);
        console.log("Districts fetched:", res.data.districts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingDistricts(false);
      }
    }
  };

  // ✅ Step 3: Handle district selection → fetch courts
  const handleDistrictSelect = async (e) => {
    const district = e.target.value;
    setSelectedDistrict(district);
    setSelectedCourt("");
    setCourts([]);
    setCaseTypes([]);
    setCaptcha(null);

    if (district) {
      setLoadingCourts(true);
      try {
        const res = await axios.post(
          "http://127.0.0.1:8000/api/set_district_and_get_courts/",
          { district },
          { headers: { Authorization: `Token ${token}` } }
        );
        setCourts(res.data.courts || []);
        console.log("Courts fetched:", res.data.courts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingCourts(false);
      }
    }
  };

  // ✅ Step 4: Handle court selection → fetch case types & captcha
  const handleCourtSelect = async (e) => {
    const court = e.target.value;
    setSelectedCourt(court);
    setCaseTypes([]);
    setCaptcha(null);
    if (court) {
      setLoadingCaseTypes(true);
      try {
        const res = await axios.post(
          "http://127.0.0.1:8000/api/set_court_and_get_case_types/",
          { court },
          { headers: { Authorization: `Token ${token}` } }
        );

        console.log("API Response:", res.data); // Add this for debugging

        setCaseTypes(res.data.case_types || []);
        setCaptcha(res.data.captcha_image || null); // Make sure this is set correctly
      } catch (err) {
        console.error("Error fetching case types:", err);
        if (err.response) {
          console.error("Response data:", err.response.data);
          console.error("Response status:", err.response.status);
        }
      } finally {
        setLoadingCaseTypes(false);
      }
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Court Case Search</h2>
      {/* Select State */}
      <div className="mb-3">
        <label className="form-label">Select State</label>
        <div className="position-relative">
          <select
            className="form-select"
            onChange={handleStateSelect}
            value={selectedState}
            disabled={loadingStates}
          >
            <option value="">-- Choose State --</option>
            {states.map((s, i) => (
              <option key={i} value={s}>
                {s}
              </option>
            ))}
          </select>
          {loadingStates && (
            <div className="position-absolute end-0 top-0 mt-2 me-2">
              <div className="spinner-border spinner-border-sm text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Select District */}
      {districts.length > 0 && (
        <div className="mb-3">
          <label className="form-label">Select District</label>
          <div className="position-relative">
            <select
              className="form-select"
              onChange={handleDistrictSelect}
              value={selectedDistrict}
              disabled={loadingDistricts}
            >
              <option value="">-- Choose District --</option>
              {districts.map((d, i) => (
                <option key={i} value={d}>
                  {d}
                </option>
              ))}
            </select>
            {loadingDistricts && (
              <div className="position-absolute end-0 top-0 mt-2 me-2">
                <div className="spinner-border spinner-border-sm text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {/* Select Court */}
      {courts.length > 1 &&
      (
        <div className="mb-3">
          <label className="form-label">Select Court</label>
          <div className="position-relative">
            <select
              className="form-select"
              onChange={handleCourtSelect}
              value={selectedCourt}
              disabled={loadingCourts}
            >
              <option value="">-- Choose Court --</option>
              {courts.map((c, i) => (
                <option key={i} value={c}>
                  {c}
                </option>
              ))}
            </select>
            {loadingCourts && (
              <div className="position-absolute end-0 top-0 mt-2 me-2">
                <div className="spinner-border spinner-border-sm text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      {/* Case Types + Captcha */}
      {loadingCaseTypes ? (
        <div className="text-center mt-3">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p>Loading case types and captcha...</p>
        </div>
      ) : (
        caseTypes.length > 0 && (
          <CaseForm
            caseTypes={caseTypes}
            captcha={captcha}  // Make sure this matches the prop name in CaseForm
            court={selectedCourt}
          />
        )
      )}
    </div>
  );
}

export default Home;

import axios from "axios";
import { useNavigate } from "react-router-dom";

const useLogout = () => {
  const navigate = useNavigate();

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
    }
  };

  const logout = async () => {
    const token = localStorage.getItem("authToken");

    handleCloseDriver();

    try {
      // Call the backend logout endpoint
      await axios.post(
        "http://127.0.0.1:8000/api/logout/",
        {},
        {
          headers: { Authorization: `Token ${token}` },
        }
      );
    } catch (error) {
      console.error("Error during logout:", error);
    } finally {
      // Remove the token from localStorage
      localStorage.removeItem("authToken");
      localStorage.removeItem("username");
      // Redirect to the login page or home page
      navigate("/login");
    }
  };

  return logout;
};

export default useLogout;

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const deliveryContent = urlParams.get("delivery_content"); // Default content for example
  const apiUrl = `/api/delivery_info?delivery_content=${deliveryContent}`;

  fetch(apiUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to fetch delivery info");
      }
      return response.json();
    })
    .then((data) => {
      if (data) {
        document.querySelector(".start-box .bold-text").textContent =
          data.edge_origin_name || "정보 없음";
        document.querySelector(".destination-box .bold-text").textContent =
          data.edge_destination_name || "정보 없음";
        document.querySelector(".final-destination .bold-text").textContent =
          data.destination || "정보 없음";
        document.querySelector(
          ".info-section .info-box .bold-text"
        ).textContent = data.content || "정보 없음";
        document.querySelector(
          ".delivery-info-container .bold-text"
        ).textContent = data.edt || "정보 없음";
      } else {
        console.error("Delivery data is empty or not found");
      }
    })
    .catch((error) => {
      console.error("Error fetching delivery info:", error);
    });
});

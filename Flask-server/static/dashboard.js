// 드론 데이터를 기반으로 카드 생성 함수
function createDroneCard(drone) {
  // 드론 카드 HTML 동적 생성
  const card = document.createElement("div");
  card.className = "drone-card";
  moving_status = "moving";
  moving_status_kr = "이동중";
  if (
    Math.sqrt(drone.vx * drone.vx + drone.vy * drone.vy + drone.vz * drone.vz) <
    0.1
  ) {
    moving_status = "stopped";
    moving_status_kr = "정지";
  } else if (Math.sqrt(drone.vx * drone.vx + drone.vy * drone.vy) < 0.1) {
    if (drone.vz > 0) {
      moving_status = "takeoff";
      moving_status_kr = "이륙";
    } else if (drone.vz < 0) {
      moving_status = "landing";
      moving_status_kr = "착륙";
    }
  }
  card.innerHTML = `
      <div class="drone-image">
          <img src="../static/assets/drone_image.jpeg" alt="드론 이미지">
      </div>
      <h3>드론 ID: ${drone.id}</h3>
      <div class="drone-info battery"><strong>배터리 상태:</strong> ${
        drone.battery_status
      }%</div>
      <div class="drone-info"><strong>현재 고도:</strong> ${
        drone.altitude
      }m</div>
      <div class="drone-info"><strong>출발지:</strong> ${
        drone.edge_origin_name
      }</div>
      <div class="drone-info"><strong>목적지:</strong> ${
        drone.edge_destination_name
      }</div>
      <div class="drone-info"><strong>최종 목적지:</strong> ${
        drone.delivery_destination
      }</div>
      <div class="drone-info"><strong>배송 물품:</strong> ${
        drone.delivery_content || "배송 물품 없음"
      }</div>
      <div class="drone-info eta"><strong>예상 소요 시간:</strong> 10분</div>
      <div class="status-indicator ${moving_status}">${moving_status_kr}</div>
  `;

  return card;
}

// 드론 데이터를 가져와 DOM에 추가
function loadDroneData() {
  fetch("/api/mission_drones") // 실제 API URL로 변경
    .then((response) => response.json())
    .then((data) => {
      const container = document.getElementById("drone-container");
      container.innerHTML = ""; // 기존 내용을 지우고 새로 추가

      data.forEach((drone) => {
        const card = createDroneCard(drone);
        container.appendChild(card); // 드론 카드를 컨테이너에 추가
      });
    })
    .catch((error) => {
      console.error("드론 데이터를 가져오는 중 오류 발생:", error);
    });
}

// 페이지 로드 시 드론 데이터 불러오기
document.addEventListener("DOMContentLoaded", loadDroneData);
setInterval(loadDroneData, 1000);

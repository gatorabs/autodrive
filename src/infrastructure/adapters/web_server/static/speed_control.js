const slider = document.getElementById("speedSlider");
const valueDisplay = document.getElementById("speedValue");
const sendButton = document.getElementById("sendSpeedButton");

const MAX_SPEED = 255;

const updateDisplay = (value) => {
  valueDisplay.textContent = value;
};

slider.addEventListener("input", () => {
  updateDisplay(slider.value);
});

async function syncSpeedFromCar() {
  try {
    const response = await fetch("/api/car-info");
    if (!response.ok) return;

    const data = await response.json();
    const carSpeed = data?.car_info?.CAR_SPEED_DATA;

    if (typeof carSpeed === "number" && !Number.isNaN(carSpeed)) {
      const clamped = Math.max(0, Math.min(Math.round(carSpeed), MAX_SPEED));
      slider.value = clamped;
      updateDisplay(clamped);
    }
  } catch (error) {
    console.warn("Não foi possível sincronizar a velocidade:", error);
  }
}

async function sendSpeed() {
  const speed = parseInt(slider.value, 10);

  try {
    const response = await fetch("/api/set-speed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speed })
    });

    const data = await response.json();

    if (data.message) {
      alert(data.message);
      await syncSpeedFromCar();
    } else if (data.error) {
      alert(data.error);
    }
  } catch (error) {
    alert("Erro ao enviar velocidade: " + error);
  }
}

sendButton.addEventListener("click", sendSpeed);

syncSpeedFromCar();

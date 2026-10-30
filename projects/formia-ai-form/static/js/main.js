// Reloj local en el footer
function updateTime() {
  const el = document.getElementById("local-time");
  if (el) {
    el.textContent = new Date().toLocaleTimeString("es-AR", {
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  }
}
updateTime();
setInterval(updateTime, 1000);

// Cerrar flash messages con click
document.querySelectorAll(".flash").forEach(f => {
  f.addEventListener("click", () => f.remove());
  setTimeout(() => f.remove(), 5000);
});

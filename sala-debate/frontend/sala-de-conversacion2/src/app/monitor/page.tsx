'use client'
import React, { useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const backend = process.env.NEXT_PUBLIC_BACKEND_URL;

// ✅ Tipos
interface ScoreData {
  usuario: string;
  mensaje: string;
  score: number;
  diagnostico: string;
}

interface TimerData {
  fase_actual: number;
  remaining_phase: number;
  elapsed_phase: number;
  remaining_total: number;
  elapsed_total: number;
  score?: number;
  diagnostico?: string;
}

interface Room {
  id: number;
  name: string;
}

const socket: Socket = io(backend!, {
  path: "/socket.io",
  transports: ["websocket"],
});

export default function MonitorPage() {
  const [room, setRoom] = useState<string>("");
  const [connectedRoom, setConnectedRoom] = useState<string | null>(null);
  const [scores, setScores] = useState<ScoreData[]>([]);
  const [timer, setTimer] = useState<TimerData | null>(null);
  const [availableRooms, setAvailableRooms] = useState<Room[]>([]);
  const [loadingRooms, setLoadingRooms] = useState<boolean>(true);
  const username = "monitor";

  // 🔹 Obtener salas disponibles desde el backend
  const fetchRooms = async () => {
    try {
      const res = await fetch(`${backend}/api/rooms`);
      if (!res.ok) throw new Error("Error al obtener salas");
      const data = await res.json();
      setAvailableRooms(data);
    } catch (error) {
      console.error("Error al cargar salas:", error);
    } finally {
      setLoadingRooms(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  // 🔹 Conectar socket a la sala seleccionada
  useEffect(() => {
    if (!connectedRoom) return;

    socket.emit("subscribe_monitor", {room:connectedRoom});
    console.log(`📡 Suscrito a la sala: ${connectedRoom}`);

    socket.on("score_update", (data: ScoreData) => {
      setScores((prev) => [data, ...prev.slice(0, 49)]);
    });

    socket.on("timer_update", (data: TimerData) => {
      console.log("⏱ timer_update recibido:", data);
      const timerScore = {
        usuario: "⏱ Timer",
        mensaje: `Fase ${data.fase_actual} | ${data.diagnostico}`,
        score: data.score ?? 0,
        diagnostico: "Evaluación automática del tiempo",
      };
      setScores(prev => [timerScore, ...prev.slice(0, 49)]);
      setTimer(data);
    });

    return () => {
      console.log(`❌ Saliendo de la sala: ${connectedRoom}`);
      socket.emit("unsubscribe_monitor", {room:connectedRoom});
      socket.off("score_update");
      socket.off("timer_update");
    };
  }, [connectedRoom]);

  useEffect(() => {
    socket.on("connect", () => {
      console.log("✅ Conectado al servidor SocketIO", socket.id);
      if (connectedRoom) {
        console.log("🔁 Re-suscribiendo monitor a", connectedRoom);
        socket.emit("subscribe_monitor", { room: connectedRoom });
      }
    });
  
    socket.on("disconnect", (reason) => {
      console.warn("⚠️ Desconectado del servidor SocketIO:", reason);
    });
  
    return () => {
      socket.off("connect");
      socket.off("disconnect");
    };
  }, [connectedRoom]);
  

  const handleJoinRoom = () => {
    if (!room) {
      alert("Debes seleccionar una sala para escuchar.");
      return;
    }
    setConnectedRoom(room);
    setScores([]);
    setTimer(null);
  };

  // ✅ Datos para el gráfico
  const chartData = [...scores]
    .reverse()
    .map((s, index) => ({
      mensaje: index + 1,
      puntaje: s.score,
    }));

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold">🎯 Monitor de Sala</h1>

      {/* 🔸 Selector de sala desde el backend */}
      <div className="mb-4">
        <label className="block mb-2 text-sm font-medium">Elige la sala:</label>
        {loadingRooms ? (
          <p className="text-gray-500 italic">Cargando salas...</p>
        ) : (
          <select
            className="border p-2 w-full rounded cursor-pointer"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
          >
            <option value="">-- Selecciona una sala --</option>
            {availableRooms.map((r) => (
              <option key={r.id} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <button
        onClick={handleJoinRoom}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition disabled:opacity-50"
        disabled={!room}
      >
        Escuchar
      </button>

      {connectedRoom && (
        <p className="text-gray-600">
          🔊 Escuchando eventos de la sala: <strong>{connectedRoom}</strong>
        </p>
      )}

      {/* 📊 Gráfico de puntajes */}
      {scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-3">📈 Evolución de Puntajes</h2>
          <div className="w-full h-64">
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="mensaje"
                  label={{ value: "N° Mensaje", position: "insideBottom", dy: 10 }}
                />
                <YAxis
                  domain={[0, 100]}
                  label={{ value: "Puntaje", angle: -90, position: "insideLeft" }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="puntaje"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* 🏆 Lista de puntuaciones con scroll */}
      <div>
        <h2 className="text-xl font-bold mb-2">🏆 Últimas puntuaciones</h2>
        <div className="max-h-80 overflow-y-auto space-y-2 border rounded-lg p-2 bg-gray-50">
          {scores.map((s, idx) => (
            <div
              key={idx}
              className="p-2 border rounded-lg bg-white shadow-sm flex justify-between"
            >
              <div>
                <strong>{s.usuario}</strong>: {s.mensaje}
              </div>
              <div className="text-green-600 font-semibold">
                {s.score}/100
                <span className="ml-2 text-gray-500 text-sm">
                  {s.diagnostico}
                </span>
              </div>
            </div>
          ))}
          {scores.length === 0 && (
            <p className="text-gray-400 italic">
              Aún no hay puntuaciones para esta sala...
            </p>
          )}
        </div>
      </div>

      {/* ⏱ Temporizador */}
      {timer && (
        <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-200">
          <h3 className="text-lg font-semibold">⏱ Temporizador</h3>
          <p>
            Fase actual: <strong>{timer.fase_actual}</strong>
          </p>
          <p>
            Tiempo restante en fase:{" "}
            <strong>{timer.remaining_phase}s</strong>
          </p>
          <p>
            Tiempo total restante:{" "}
            <strong>{timer.remaining_total}s</strong>
          </p>
        </div>
      )}
    </div>
  );
}

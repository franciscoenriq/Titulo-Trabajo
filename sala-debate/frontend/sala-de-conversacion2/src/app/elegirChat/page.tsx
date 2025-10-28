'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthGuard } from '../hooks/useAuthGuard'
import PromptsPage from '../components/prompts'
import MultiAgentConfigPage from '../components/multiAgentConfig'
import RoomConfig from '../components/RoomConfig'
import TemasManager from '../components/temasManager'

export default function Home() {
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const [activeTab, setActiveTab] = useState<'sala' | 'prompts' | 'multiagente' | 'temas'>('sala')
  
  return (
    <main className="flex justify-center items-center min-h-screen ">
      <div className="relative bg-white shadow-lg rounded-2xl max-w-7xl w-[150vh] h-[90vh] p-6 overflow-y-auto">
        
        {/* Barra superior con botones de pestañas */}
        <div className="flex space-x-4 border-b pb-2 mb-4">
          <button
            onClick={() => setActiveTab('prompts')}
            className={`px-4 py-1 rounded-t-md font-medium ${activeTab === 'prompts' ? 'bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            Ver Prompts de Agentes
          </button>
          <button
            onClick={() => setActiveTab('multiagente')}
            className={`px-4 py-1 rounded-t-md font-medium ${activeTab === 'multiagente' ? 'bg-purple-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            Configuración Multiagente
          </button>
          <button
            onClick={() => setActiveTab('sala')}
            className={`px-4 py- rounded-t-md font-medium ${activeTab === 'sala' ? 'bg-green-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            Configuración de la Sala
          </button>
          <button
          onClick={() => setActiveTab('temas')}
          className={`px-4 py- rounded-t-md font-medium ${activeTab === 'temas' ? 'bg-green-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}
          >
            Temas para Debates
          </button>
        </div>

        {/* Contenido de las pestañas */}
        <div className="mt-4">
          {activeTab === 'prompts' && <PromptsPage />}
          {activeTab === 'multiagente' && <MultiAgentConfigPage />}
          {activeTab === 'sala' && <RoomConfig backend={backend!} />}  
          {activeTab === 'temas' && <TemasManager backend={backend!} />} 
        </div>
      </div>
    </main>
  )
}

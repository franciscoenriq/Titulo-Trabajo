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
  const router = useRouter()
  
  return (
    <main className="flex justify-center items-start min-h-screen pt-12">
      <div className="relative bg-white shadow-lg rounded-2xl max-w-7xl w-[150vh] h-[90vh] p-6 overflow-y-auto mt-6 md:mt-8">
        
        {/* Barra superior con botones de pestañas */}
        <div className="flex items-center gap-2 border-b pb-2 mb-4">
          
          <button
            onClick={() => setActiveTab('prompts')}
            className={`px-3 py-1 text-sm rounded-md font-medium transition ${
              activeTab === 'prompts' ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            Prompts
          </button>

          <button
            onClick={() => setActiveTab('multiagente')}
            className={`px-3 py-1 text-sm rounded-md font-medium transition ${
              activeTab === 'multiagente' ? 'bg-purple-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            Multiagente
          </button>
          
          <button
            onClick={() => setActiveTab('sala')}
            className={`px-3 py-1 text-sm rounded-md font-medium transition ${
              activeTab === 'sala' ? 'bg-green-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            Sala
          </button>

          <button
            onClick={() => setActiveTab('temas')}
            className={`px-3 py-1 text-sm rounded-md font-medium transition ${
              activeTab === 'temas' ? 'bg-green-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            Temas
          </button>
          <button
            onClick={() => router.push('/historicalChatConversation')}
            className="px-3 py-1 text-sm rounded-md font-medium bg-yellow-600 text-white hover:bg-yellow-700 transition"
          >
            Histórico
          </button>
          {/*
          <button
            onClick={() => router.push('/visualizacion')}
            className="px-3 py-1 text-sm rounded-md font-medium bg-yellow-600 text-white hover:bg-yellow-700 transition"
          >

            Graficos
          </button>
          */}
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

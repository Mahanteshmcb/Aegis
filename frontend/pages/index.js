import Head from 'next/head'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import Main from '../components/Main'
import Button from '../components/Button'
import Card from '../components/Card'
import Form from '../components/Form'

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <Main>
          <Card className="max-w-md mx-auto">
            <h1 className="text-4xl font-bold text-blue-600 mb-4">
              Welcome to <span className="underline">Aegis</span>
            </h1>
            <p className="text-lg text-gray-700 mb-6">
              Sovereign Asset Management Platform
            </p>
            <Form>
              <Button type="button">Get Started</Button>
            </Form>
          </Card>
        </Main>
      </div>
    </div>
  )
}
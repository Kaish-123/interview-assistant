import { NextRequest, NextResponse } from 'next/server'
import { getAllClients, addClient, updateClient, deleteClient } from '@/lib/db'

export async function GET() {
  try {
    const clients = getAllClients()
    return NextResponse.json({ clients })
  } catch (error) {
    console.error('Error fetching clients:', error)
    return NextResponse.json({ error: 'Failed to fetch clients' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, rate, keywords } = body

    if (!name || !rate) {
      return NextResponse.json({ error: 'Name and rate are required' }, { status: 400 })
    }

    const client = addClient(name, parseInt(rate, 10), keywords)
    return NextResponse.json({ client })
  } catch (error: any) {
    console.error('Error adding client:', error)
    if (error.message?.includes('UNIQUE')) {
      return NextResponse.json({ error: 'Client already exists' }, { status: 400 })
    }
    return NextResponse.json({ error: 'Failed to add client' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, name, rate, keywords } = body

    if (!id || !name || !rate) {
      return NextResponse.json({ error: 'ID, name and rate are required' }, { status: 400 })
    }

    const client = updateClient(id, name, parseInt(rate, 10), keywords)
    return NextResponse.json({ client })
  } catch (error) {
    console.error('Error updating client:', error)
    return NextResponse.json({ error: 'Failed to update client' }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json({ error: 'ID is required' }, { status: 400 })
    }

    deleteClient(parseInt(id, 10))
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting client:', error)
    return NextResponse.json({ error: 'Failed to delete client' }, { status: 500 })
  }
}


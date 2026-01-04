import { useState } from 'react'
import axios from 'axios'
import { useRouter } from 'next/router'

export default function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const router = useRouter()

  async function submit(e){
    e.preventDefault()
    try{
      const fd = new URLSearchParams()
      fd.append('username', username)
      fd.append('password', password)
      const res = await axios.post('http://localhost:8000/login', fd, {
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
      })
      localStorage.setItem('token', res.data.access_token)
      router.push('/chat')
    }catch(err){
      alert('Login gagal: ' + (err.response?.data?.detail || err.message))
    }
  }

  return (
    <div style={{maxWidth:420, margin:'40px auto'}}>
      <h2>Panglima Mayu Chatbot — Login</h2>
      <form onSubmit={submit}>
        <label>Username</label>
        <input value={username} onChange={e=>setUsername(e.target.value)} />
        <label>Password</label>
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit">Login</button>
      </form>
    </div>
  )
}

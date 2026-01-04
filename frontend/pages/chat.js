import { useState, useEffect } from 'react'
import axios from 'axios'
import { useRouter } from 'next/router'

export default function Chat(){
  const [q, setQ] = useState('')
  const [resp, setResp] = useState(null)
  const router = useRouter()

  useEffect(()=>{
    const t = localStorage.getItem('token')
    if(!t) router.push('/')
  }, [])

  async function ask(e){
    e.preventDefault()
    try{
      const token = localStorage.getItem('token')
      const res = await axios.post('http://localhost:8000/chat', {query: q}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setResp(res.data)
    }catch(err){
      alert('Error: ' + (err.response?.data?.detail || err.message))
    }
  }

  return (
    <div style={{maxWidth:800, margin:'24px auto'}}>
      <h2>Panglima Mayu — Chat</h2>
      <form onSubmit={ask}>
        <input value={q} onChange={e=>setQ(e.target.value)} style={{width:'100%'}} />
        <button type="submit">Tanya</button>
      </form>
      {resp && (
        <div style={{marginTop:20}}>
          <h3>Jawaban</h3>
          <div>{resp.answer}</div>
          <h4>Sumber</h4>
          <pre>{JSON.stringify(resp.sources, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

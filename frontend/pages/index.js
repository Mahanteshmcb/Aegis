import Head from 'next/head'
import styles from '../styles/Home.module.css'

export default function Home() {
  return (
    <div className={styles.container}>
      <Head>
        <title>Aegis Dashboard</title>
        <meta name="description" content="Decentralized Digital Twin Framework" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to <a href="#">Aegis</a>
        </h1>

        <p className={styles.description}>
          Sovereign Asset Management Platform
        </p>
      </main>
    </div>
  )
}
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { profilesApi } from '../api'

const ProfilesContext = createContext()

export function ProfilesProvider({ children }) {
    const [profiles, setProfiles] = useState([])
    const [loading, setLoading] = useState(false)

    // Fetch profiles from backend on mount
    const fetchProfiles = useCallback(async () => {
        setLoading(true)
        try {
            const { data } = await profilesApi.getAll()
            setProfiles(data)
        } catch (err) {
            console.error('Failed to fetch profiles:', err)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchProfiles()
    }, [fetchProfiles])

    const addProfile = async (name) => {
        try {
            const { data } = await profilesApi.create({ name: name.trim(), accounts: [] })
            setProfiles(p => [...p, data])
            return data
        } catch (err) {
            console.error('Failed to create profile:', err)
            // Fallback to local-only
            const newProfile = { id: `profile-${Date.now()}`, name: name.trim(), accounts: [] }
            setProfiles(p => [...p, newProfile])
            return newProfile
        }
    }

    const deleteProfile = async (id) => {
        try {
            await profilesApi.delete(id)
        } catch (err) {
            console.error('Failed to delete profile:', err)
        }
        setProfiles(p => p.filter(x => x.id !== id))
    }

    const linkAccount = (profileId, accountId) => {
        setProfiles(p => p.map(prof =>
            prof.id === profileId
                ? { ...prof, accounts: [...(prof.accounts || []), accountId] }
                : prof
        ))
    }

    return (
        <ProfilesContext.Provider value={{ profiles, loading, addProfile, deleteProfile, linkAccount, fetchProfiles }}>
            {children}
        </ProfilesContext.Provider>
    )
}

export function useProfiles() {
    const ctx = useContext(ProfilesContext)
    if (!ctx) throw new Error('useProfiles must be used within a ProfilesProvider')
    return ctx
}

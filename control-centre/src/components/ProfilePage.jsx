import React, { useState, useEffect } from 'react';
import { User, Mail, Building, Calendar, Shield, Edit2, Save, X } from 'lucide-react';
import { getUserProfile, updateUserProfile } from '../api/profileApi';
import './ProfilePage.css';

const ProfilePage = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUserProfile();
      setProfile(data);
      setEditedProfile(data);
    } catch (err) {
      setError(err.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditing(true);
    setEditedProfile({ ...profile });
    setSaveSuccess(false);
  };

  const handleCancel = () => {
    setEditing(false);
    setEditedProfile({ ...profile });
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateUserProfile(editedProfile);
      setProfile(updated);
      setEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setEditedProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">
          <div className="spinner"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="profile-page">
        <div className="profile-error">
          <p>{error}</p>
          <button onClick={loadProfile} className="retry-button">Retry</button>
        </div>
      </div>
    );
  }

  const displayProfile = editing ? editedProfile : profile;

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>User Profile</h1>
        {!editing ? (
          <button onClick={handleEdit} className="edit-button">
            <Edit2 size={18} />
            Edit Profile
          </button>
        ) : (
          <div className="edit-actions">
            <button onClick={handleCancel} className="cancel-button" disabled={saving}>
              <X size={18} />
              Cancel
            </button>
            <button onClick={handleSave} className="save-button" disabled={saving}>
              <Save size={18} />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>

      {saveSuccess && (
        <div className="success-message">
          Profile updated successfully!
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="profile-content">
        <div className="profile-section avatar-section">
          <div className="avatar-container">
            {displayProfile?.avatar ? (
              <img src={displayProfile.avatar} alt="Profile" className="avatar" />
            ) : (
              <div className="avatar-placeholder">
                <User size={64} />
              </div>
            )}
          </div>
          {editing && (
            <div className="avatar-edit">
              <input
                type="text"
                placeholder="Avatar URL"
                value={editedProfile.avatar || ''}
                onChange={(e) => handleInputChange('avatar', e.target.value)}
                className="form-input"
              />
            </div>
          )}
        </div>

        <div className="profile-section details-section">
          <h2>Personal Information</h2>
          <div className="profile-fields">
            <div className="profile-field">
              <div className="field-label">
                <User size={18} />
                <span>Full Name</span>
              </div>
              {editing ? (
                <input
                  type="text"
                  value={editedProfile.name || ''}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="form-input"
                  placeholder="Enter your name"
                />
              ) : (
                <div className="field-value">{displayProfile?.name || 'Not set'}</div>
              )}
            </div>

            <div className="profile-field">
              <div className="field-label">
                <Mail size={18} />
                <span>Email</span>
              </div>
              {editing ? (
                <input
                  type="email"
                  value={editedProfile.email || ''}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="form-input"
                  placeholder="Enter your email"
                />
              ) : (
                <div className="field-value">{displayProfile?.email || 'Not set'}</div>
              )}
            </div>

            <div className="profile-field">
              <div className="field-label">
                <Building size={18} />
                <span>Organization</span>
              </div>
              {editing ? (
                <input
                  type="text"
                  value={editedProfile.organization || ''}
                  onChange={(e) => handleInputChange('organization', e.target.value)}
                  className="form-input"
                  placeholder="Enter your organization"
                />
              ) : (
                <div className="field-value">{displayProfile?.organization || 'Not set'}</div>
              )}
            </div>

            <div className="profile-field">
              <div className="field-label">
                <Shield size={18} />
                <span>Role</span>
              </div>
              {editing ? (
                <select
                  value={editedProfile.role || 'developer'}
                  onChange={(e) => handleInputChange('role', e.target.value)}
                  className="form-select"
                >
                  <option value="developer">Developer</option>
                  <option value="project_manager">Project Manager</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
              ) : (
                <div className="field-value role-badge">
                  {displayProfile?.role || 'developer'}
                </div>
              )}
            </div>

            <div className="profile-field">
              <div className="field-label">
                <Calendar size={18} />
                <span>Member Since</span>
              </div>
              <div className="field-value">
                {displayProfile?.createdAt
                  ? new Date(displayProfile.createdAt).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                  : 'Unknown'}
              </div>
            </div>
          </div>
        </div>

        <div className="profile-section preferences-section">
          <h2>Preferences</h2>
          <div className="profile-fields">
            <div className="profile-field">
              <div className="field-label">
                <span>Notifications</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={displayProfile?.preferences?.notifications ?? true}
                  onChange={(e) =>
                    handleInputChange('preferences', {
                      ...editedProfile.preferences,
                      notifications: e.target.checked
                    })
                  }
                  disabled={!editing}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="profile-field">
              <div className="field-label">
                <span>Email Updates</span>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={displayProfile?.preferences?.emailUpdates ?? false}
                  onChange={(e) =>
                    handleInputChange('preferences', {
                      ...editedProfile.preferences,
                      emailUpdates: e.target.checked
                    })
                  }
                  disabled={!editing}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
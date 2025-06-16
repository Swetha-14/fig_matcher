import React, { useState, useEffect } from 'react';
import { Search, Users, ArrowRight, User, MessageCircle, MapPin, Clock, X, ChevronRight, Activity, Star, Zap, Lightbulb } from 'lucide-react';
import './App.css';

interface User {
  id: number;
  name: string;
  bio: string;
  location?: string;
  activity_status?: string;
  domain_expertise?: string[];
  current_role?: string;
  experience_level?: string;
  networking_intent?: string;
  conversations?: Array<{
    text: string;
    timestamp: string;
  }>;
  conversation_count?: number;
  remote_preference?: string;
  last_active?: string;
}

interface SearchResult extends User {
  user_id: number;
  similarity_score: number;
  similarity_percentage: number;
  explanation?: string;
  rank?: number;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_found: number;
  search_time_ms: number;
  top_match_explanation?: string;
  status: string;
  error_message?: string;
  suggestions?: string[];
}

interface UsersResponse {
  users: User[];
  total: number;
  timestamp: number;
}

const CleanFigboxMatcher: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedProfile, setSelectedProfile] = useState<number | 'guest'>('guest');
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [profileModalOpen, setProfileModalOpen] = useState<boolean>(false);
  const [selectedUserDetails, setSelectedUserDetails] = useState<User | SearchResult | null>(null);
  const [topMatch, setTopMatch] = useState<SearchResult | null>(null);
  const [topMatchExplanation, setTopMatchExplanation] = useState<string>('');
  const [searchTime, setSearchTime] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    fetchAllUsers();
  }, []);

  const fetchAllUsers = async (): Promise<void> => {
    try {
      const response = await fetch('http://localhost:8000/users');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: UsersResponse = await response.json();
      setAllUsers(data.users || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setErrorMessage('Failed to load users. Please check if the backend is running.');
    }
  };

  const handleSearch = async (): Promise<void> => {
    if (!query.trim()) return;

    setLoading(true);
    setTopMatch(null);
    setTopMatchExplanation('');
    setResults([]);
    setErrorMessage('');

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          k: 10,
          current_user_id: selectedProfile === 'guest' ? null : selectedProfile,
          min_similarity_threshold: 0.1
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();

      if (data.status === 'error' || data.error_message) {
        setErrorMessage(data.error_message || 'Search failed');
        return;
      }

      setSearchTime(data.search_time_ms || 0);

      if (data.results && data.results.length > 0) {
        // First result is the top match
        const topResult = data.results[0];
        setTopMatch(topResult);
        setTopMatchExplanation(data.top_match_explanation || '');

        const otherResults = data.results.slice(1);
        setResults(otherResults);
      } else {
        setErrorMessage('No matches found. Try different keywords or a more specific query.');
      }
    } catch (error) {
      console.error('Search failed:', error);
      setErrorMessage('Search failed. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSwitch = (userId: number | 'guest'): void => {
    setSelectedProfile(userId);
    setResults([]);
    setTopMatch(null);
    setTopMatchExplanation('');
    setSidebarOpen(false);
    setQuery('');
    setErrorMessage('');
  };

  const showProfileDetails = (user: User | SearchResult): void => {
    setSelectedUserDetails(user);
    setProfileModalOpen(true);
  };

  const getProfileImage = (userId: number | 'guest'): string => {
    const images: Record<number | 'guest', string> = {
      1: '👨‍💻', 2: '👩‍🔬', 3: '👨‍💼', 4: '👩‍💻', 5: '👨‍💼',
      6: '👩‍💼', 7: '👨‍💻', 8: '👩‍💼', 9: '👨‍💼', 10: '👩‍💼',
      'guest': '👤'
    };
    return images[userId] || '👤';
  };

  const getProfileColor = (userId: number | 'guest'): string => {
    const colors: Record<number | 'guest', string> = {
      1: '#3b82f6', 2: '#10b981', 3: '#f59e0b', 4: '#ef4444', 5: '#8b5cf6',
      6: '#06b6d4', 7: '#84cc16', 8: '#f97316', 9: '#ec4899', 10: '#6366f1',
      'guest': '#64748b'
    };
    return colors[userId] || '#64748b';
  };

  const getGreeting = (): string => {
    if (selectedProfile === 'guest') {
      return "Hi! Who would you love to meet right now?";
    }
    const user = allUsers.find(u => u.id === selectedProfile);
    return user ? `Hi ${user.name.split(' ')[0]}! Who would you love to meet right now?` : "Hi! Who would you love to meet right now?";
  };

  const getActivityColor = (status?: string): string => {
    switch (status) {
      case 'active': return '#10b981';
      case 'recent': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getActivityText = (status?: string): string => {
    switch (status) {
      case 'active': return 'Active';
      case 'recent': return 'Recently Active';
      default: return 'Offline';
    }
  };

  const getInitials = (name: string): string => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatRole = (role?: string): string => {
    if (!role) return '';
    return role.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatExperience = (level?: string): string => {
    if (!level) return '';
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="sidebar-content">
          <div className="sidebar-header">
            <div className="sidebar-title">
              <Users size={20} className="sidebar-icon" />
              <h3 className="sidebar-heading">Users</h3>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="sidebar-close-btn"
            >
              <X size={18} />
            </button>
          </div>

          <div className="user-profiles">
            {/* Guest Profile */}
            <div className="profile-row">
              <button
                onClick={() => handleProfileSwitch('guest')}
                className={`profile-btn ${selectedProfile === 'guest' ? 'profile-btn-selected' : 'profile-btn-default'}`}
              >
                <div className={`profile-avatar ${selectedProfile === 'guest' ? 'profile-avatar-selected' : ''}`} style={{ backgroundColor: getProfileColor('guest') }}>
                  👤
                </div>
                <div className="profile-info">
                  <div className="profile-name">Guest</div>
                  <div className="profile-status">Explore freely</div>
                </div>
              </button>
            </div>

            {/* User Profiles */}
            {allUsers.map(user => (
              <div key={user.id} className="profile-row">
                <button
                  onClick={() => handleProfileSwitch(user.id)}
                  className={`profile-btn ${selectedProfile === user.id ? 'profile-btn-selected' : 'profile-btn-default'}`}
                >
                  <div className={`profile-avatar ${selectedProfile === user.id ? 'profile-avatar-selected' : ''}`} style={{ backgroundColor: getProfileColor(user.id) }}>
                    {getInitials(user.name)}
                    <div className="activity-indicator" style={{ backgroundColor: getActivityColor(user.activity_status) }}></div>
                  </div>
                  <div className="profile-info">
                    <div className="profile-name">{user.name}</div>
                    <div className="profile-status">
                      {getActivityText(user.activity_status)}
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => showProfileDetails(user)}
                  className="profile-details-btn"
                  style={{
                    '--hover-color': getProfileColor(user.id)
                  } as React.CSSProperties}
                >
                  <User size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="sidebar-toggle-btn"
      >
        <Users size={16} />
        <span>Users</span>
        <ChevronRight size={14} />
      </button>

      {/* Main Content */}
      <div className="main-content">
        {/* Logo */}
        <div className="logo">
          <div className="logo-icon">
            <Users size={24} />
          </div>
          <span className="logo-text">
            Figbox
          </span>
        </div>

        {/* Greeting */}
        <h1 className="greeting">
          {getGreeting()}
        </h1>

        {/* Search */}
        <div className="search-container">
          <div className="search-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="AI co-founder in fintech, climate tech expert, React developer..."
              className="search-input"
            />
            <Search className="search-icon" size={20} />
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className={`search-btn ${loading || !query.trim() ? 'search-btn-disabled' : 'search-btn-enabled'}`}
          >
            {loading ? (
              <>
                <div className="loading-spinner"></div>
                Finding matches...
              </>
            ) : (
              <>
                Find matches
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div className="error-message">
            <X size={16} />
            {errorMessage}
          </div>
        )}

        {/* Top Match Section */}
        {topMatch && (
          <div className="best-match-section">
            <div className="section-header">
              <Star size={20} className="section-icon" />
              <h2 className="section-title">
                Perfect Match
              </h2>
              {searchTime > 0 && (
                <span className="search-time">
                  Found in {Math.round(searchTime)}ms
                </span>
              )}
            </div>

            <div
              className="best-match-card"
              onClick={() => showProfileDetails(topMatch)}
            >
              <div className="best-match-badge">
                <Zap size={14} />
                {topMatch.similarity_percentage}% match
              </div>

              <div className="best-match-header">
                <div className="best-match-avatar">
                  {getInitials(topMatch.name)}
                  <div className="activity-indicator activity-indicator-large" style={{ backgroundColor: getActivityColor(topMatch.activity_status) }}></div>
                </div>
                <div className="best-match-info">
                  <h3 className="best-match-name">
                    {topMatch.name}
                  </h3>
                  <div className="best-match-location">
                    <MapPin size={14} />
                    {topMatch.location}
                  </div>
                  <div className="best-match-role">
                    {formatRole(topMatch.current_role)} • {formatExperience(topMatch.experience_level)}
                  </div>
                </div>
              </div>

              {topMatchExplanation && (
                <div className="best-match-explanation">
                  <h4 className="explanation-title">
                    <Lightbulb size={16} />
                    Why this is a perfect match
                  </h4>
                  <p className="explanation-text">
                    {topMatchExplanation}
                  </p>
                </div>
              )}

              <p className="best-match-bio">
                {topMatch.bio}
              </p>

              {topMatch.domain_expertise && topMatch.domain_expertise.length > 0 && (
                <div className="expertise-tags">
                  {topMatch.domain_expertise.map((domain, index) => (
                    <span key={index} className="expertise-tag">
                      {domain}
                    </span>
                  ))}
                </div>
              )}

              <button className="connect-btn best-match-connect">
                <MessageCircle size={16} />
                Connect with {topMatch.name.split(' ')[0]}
              </button>
            </div>
          </div>
        )}

        {/* Other Results */}
        {results.length > 0 && (
          <div className="results-section">
            <div className="section-header">
              <Users size={20} />
              <h2 className="section-title">
                Other great matches ({results.length})
              </h2>
            </div>

            <div className="results-grid">
              {results.map((result) => (
                <div
                  key={result.user_id}
                  className="result-card"
                  onClick={() => showProfileDetails(result)}
                >
                  <div className="result-header">
                    <div className="result-avatar" style={{ backgroundColor: getProfileColor(result.user_id) }}>
                      {getInitials(result.name)}
                      <div className="activity-indicator" style={{ backgroundColor: getActivityColor(result.activity_status) }}></div>
                    </div>
                    <div className="result-info">
                      <h3 className="result-name">
                        {result.name}
                      </h3>
                      <div className="match-percentage">
                        {result.similarity_percentage}% match
                      </div>
                    </div>
                  </div>

                  <div className="result-role">
                    {formatRole(result.current_role)} • {formatExperience(result.experience_level)}
                  </div>

                  <p className="result-bio">
                    {result.bio}
                  </p>

                  {result.location && (
                    <div className="result-location">
                      <MapPin size={14} />
                      {result.location}
                    </div>
                  )}

                  {result.domain_expertise && result.domain_expertise.length > 0 && (
                    <div className="result-expertise">
                      {result.domain_expertise.slice(0, 3).map((domain, index) => (
                        <span key={index} className="result-expertise-tag">
                          {domain}
                        </span>
                      ))}
                    </div>
                  )}

                  <button className="connect-btn">
                    <MessageCircle size={14} />
                    Connect
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {results.length === 0 && !topMatch && query && !loading && !errorMessage && (
          <div className="no-results">
            <Search size={48} />
            <h3>No matches found</h3>
            <p>Try different keywords or make your query more specific!</p>
          </div>
        )}
      </div>

      {/* Profile Details Modal */}
      {profileModalOpen && selectedUserDetails && (
        <div className="modal-overlay" onClick={() => setProfileModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                Profile Details
              </h2>
              <button
                onClick={() => setProfileModalOpen(false)}
                className="modal-close-btn"
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-profile-header">
              <div className="modal-avatar" style={{ backgroundColor: getProfileColor('user_id' in selectedUserDetails ? selectedUserDetails.user_id : selectedUserDetails.id || 1) }}>
                {getInitials(selectedUserDetails.name)}
                <div className="activity-indicator activity-indicator-large" style={{ backgroundColor: getActivityColor(selectedUserDetails.activity_status) }}></div>
              </div>
              <div className="modal-profile-info">
                <h3 className="modal-profile-name">
                  {selectedUserDetails.name}
                </h3>
                <div className="modal-profile-status">
                  <Activity size={14} />
                  <span>{getActivityText(selectedUserDetails.activity_status)}</span>
                </div>
                {'current_role' in selectedUserDetails && selectedUserDetails.current_role && (
                  <div className="modal-profile-role">
                    {formatRole(selectedUserDetails.current_role)} • {formatExperience(selectedUserDetails.experience_level)}
                  </div>
                )}
              </div>
            </div>

            <p className="modal-bio">
              {selectedUserDetails.bio}
            </p>

            {selectedUserDetails.domain_expertise && selectedUserDetails.domain_expertise.length > 0 && (
              <div className="modal-expertise-section">
                <h4 className="modal-section-title">
                  Domain Expertise
                </h4>
                <div className="modal-expertise-tags">
                  {selectedUserDetails.domain_expertise.map((domain, index) => (
                    <span key={index} className="modal-expertise-tag">
                      {domain}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {'networking_intent' in selectedUserDetails && selectedUserDetails.networking_intent && (
              <div className="modal-networking-section">
                <h4 className="modal-section-title">
                  Networking Intent
                </h4>
                <div className="modal-networking-intent">
                  {formatRole(selectedUserDetails.networking_intent)}
                </div>
              </div>
            )}

            {selectedUserDetails.conversations && selectedUserDetails.conversations.length > 0 && (
              <div className="modal-conversations-section">
                <h4 className="modal-section-title">
                  <MessageCircle size={16} />
                  Recent Activity
                </h4>
                <div className="conversations-list">
                  {selectedUserDetails.conversations.slice(0, 5).map((conversation, index) => (
                    <div key={index} className="conversation-item">
                      <p className="conversation-text">
                        {conversation.text}
                      </p>
                      <div className="conversation-timestamp">
                        <Clock size={12} />
                        {conversation.timestamp}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CleanFigboxMatcher;
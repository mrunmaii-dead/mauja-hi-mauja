import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import styles from './KeywordForm.module.css';

function KeywordForm() {
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [selectedKeyword, setSelectedKeyword] = useState('');

  // Get the IP address from the URL parameters using useParams
  const { ip } = useParams();  // `ip` is the dynamic part of the URL

  // Determine the base URL based on the IP from the URL
  const baseURL = ip ? `http://${ip}:5001` : 'http://localhost:5000';

  // Fetch the keywords from the server on component load
  useEffect(() => {
    const fetchKeywords = async () => {
      try {
        const response = await axios.get(`${baseURL}/keywords`);
        setKeywords(response.data.keywords);
      } catch (error) {
        console.error("Error fetching keywords:", error);
      }
    };
    fetchKeywords();
  }, [baseURL]);

  // Add a new keyword
  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;

    try {
      const response = await axios.post(`${baseURL}/keywords`, { keyword: newKeyword });
      if (response.status === 200) {
        setKeywords(response.data.keywords); // Update with the new keyword list from the server
        setNewKeyword(''); // Clear the input field
      }
    } catch (error) {
      console.error("Error adding keyword:", error);
    }
  };

  // Delete the selected keyword
  const handleDeleteKeyword = async () => {
    if (!selectedKeyword) return;

    try {
      const response = await axios.delete(`${baseURL}/keywords/${selectedKeyword}`);
      if (response.status === 200) {
        setKeywords(response.data.keywords); // Update with the new keyword list from the server
        setSelectedKeyword(''); // Clear selection after deletion
      }
    } catch (error) {
      console.error("Error deleting keyword:", error);
    }
  };

  return (
    <div className={styles.keywordForm}>
      <div className={styles.inputSection}>
        <label htmlFor="keywordInput" className={styles.inputLabel}>
          Add a Keyword to Restrict
        </label>
        <input
          type="text"
          id="keywordInput"
          value={newKeyword}
          onChange={(e) => setNewKeyword(e.target.value)}
          className={styles.keywordInput}
          placeholder="Enter keyword here"
        />
        <button onClick={handleAddKeyword} className={styles.addButton}>Add</button>
      </div>
      <div className={styles.selectedSection}>
        <label htmlFor="selectedKeywords" className={styles.inputLabel}>
          Current Keywords
        </label>
        <select
          id="selectedKeywords"
          className={styles.selectDropdown}
          value={selectedKeyword}
          onChange={(e) => setSelectedKeyword(e.target.value)}
        >
          <option value="" disabled>Select a keyword</option>
          {keywords.map((keyword, index) => (
            <option key={index} value={keyword}>
              {keyword}
            </option>
          ))}
        </select>
        <button
          onClick={handleDeleteKeyword}
          className={styles.deleteButton}
          disabled={!selectedKeyword}
        >
          Delete Selected Keyword
        </button>
      </div>
    </div>
  );
}

export default KeywordForm;

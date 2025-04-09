import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  // User state
  const [username, setUsername] = useState(() => {
    return localStorage.getItem("infiniteCraftUsername") || "";
  });
  const [showUsernameModal, setShowUsernameModal] = useState(!localStorage.getItem("infiniteCraftUsername"));
  
  // Game state
  const [baseElements, setBaseElements] = useState([]);
  const [discoveredElements, setDiscoveredElements] = useState([]);
  const [workspaceElements, setWorkspaceElements] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedElement, setDraggedElement] = useState(null);
  const [discoveryCount, setDiscoveryCount] = useState(0);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [combinationResult, setCombinationResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  // Removed tabs state
  const workspaceRef = useRef(null);
  const resultTimeoutRef = useRef(null);
  
  // Canvas animation for subtle effects
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  
  // Handle username submission
  const handleUsernameSubmit = (e) => {
    e.preventDefault();
    if (username.trim()) {
      localStorage.setItem("infiniteCraftUsername", username.trim());
      setShowUsernameModal(false);
      // Fetch data with the new username
      fetchBaseElements();
      fetchDiscoveredElements();
      fetchUserProgress();
    }
  };

  // Fetch base elements and discovered elements on load
  useEffect(() => {
    fetchBaseElements();
    fetchDiscoveredElements();
    fetchUserProgress();
  }, []);
  
  // Log elements for debugging
  useEffect(() => {
    console.log('Base Elements:', baseElements);
    console.log('Discovered Elements:', discoveredElements);
  }, [baseElements, discoveredElements]);

  // Set up canvas animation
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const particles = [];
    const particleCount = 50;
    
    // Resize canvas to match parent
    const resizeCanvas = () => {
      if (workspaceRef.current) {
        canvas.width = workspaceRef.current.offsetWidth;
        canvas.height = workspaceRef.current.offsetHeight;
      }
    };
    
    // Create particles
    const createParticles = () => {
      for (let i = 0; i < particleCount; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          radius: Math.random() * 2 + 1,
          color: `rgba(230, 230, 230, ${Math.random() * 0.2 + 0.1})`,
          speedX: Math.random() * 0.5 - 0.25,
          speedY: Math.random() * 0.5 - 0.25
        });
      }
    };
    
    // Draw and animate particles
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach(particle => {
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.fill();
        
        // Move particle
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        
        // Boundary check
        if (particle.x < 0 || particle.x > canvas.width) {
          particle.speedX = -particle.speedX;
        }
        
        if (particle.y < 0 || particle.y > canvas.height) {
          particle.speedY = -particle.speedY;
        }
      });
      
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    
    // Initialize
    resizeCanvas();
    createParticles();
    animate();
    
    // Handle resize
    window.addEventListener('resize', resizeCanvas);
    
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (resultTimeoutRef.current) {
        clearTimeout(resultTimeoutRef.current);
      }
    };
  }, []);

  const fetchBaseElements = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/elements/base`);
      const data = await response.json();
      console.log("Raw base elements data:", data);
      setBaseElements(data);
    } catch (error) {
      console.error("Error fetching base elements:", error);
    }
  };

  const fetchDiscoveredElements = async () => {
    try {
      const userId = localStorage.getItem("infiniteCraftUsername") || "default";
      console.log(`Fetching discovered elements for user: ${userId}`);
      const response = await fetch(
        `${BACKEND_URL}/api/elements/discovered?user_id=${userId}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log("Discovered elements data:", data);
      setDiscoveredElements(data);
    } catch (error) {
      console.error("Error fetching discovered elements:", error);
      // Set base elements as fallback if we can't get discovered elements
      if (baseElements.length > 0) {
        setDiscoveredElements(baseElements);
      }
    }
  };

  const fetchUserProgress = async () => {
    try {
      const userId = localStorage.getItem("infiniteCraftUsername") || "default";
      const response = await fetch(
        `${BACKEND_URL}/api/user/progress?user_id=${userId}`
      );
      const data = await response.json();
      setDiscoveryCount(data.discovery_count);
    } catch (error) {
      console.error("Error fetching user progress:", error);
    }
  };

  const resetProgress = async () => {
    try {
      const userId = localStorage.getItem("infiniteCraftUsername") || "default";
      await fetch(`${BACKEND_URL}/api/user/reset?user_id=${userId}`, {
        method: "POST",
      });
      // Refresh data
      fetchBaseElements();
      fetchDiscoveredElements();
      fetchUserProgress();
      setWorkspaceElements([]);
    } catch (error) {
      console.error("Error resetting progress:", error);
    }
  };
  
  const clearWorkspace = () => {
    setWorkspaceElements([]);
  };

  // Generate a unique ID for workspace elements
  const generateWorkspaceId = () => {
    return `workspace-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  };

  // Handle drag start from element library
  const handleDragStart = (element, event) => {
    event.preventDefault();
    
    if (event.type === "mousedown") {
      // For mouse events, calculate offset relative to the element
      const rect = event.currentTarget.getBoundingClientRect();
      setDragOffset({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      });
    } else {
      // For touch events, use a default offset
      setDragOffset({ x: 30, y: 30 });
    }

    setIsDragging(true);
    setDraggedElement({
      ...element,
      workspaceId: generateWorkspaceId(),
      position: { x: 0, y: 0 },
    });
    
    console.log("Started dragging element:", element.name);
  };

  // Handle drag over workspace
  const handleDragOver = (event) => {
    event.preventDefault();
    if (!isDragging || !draggedElement) return;

    // Update the position for visual feedback
    const workspaceRect = workspaceRef.current.getBoundingClientRect();
    const x = event.clientX - workspaceRect.left - dragOffset.x;
    const y = event.clientY - workspaceRect.top - dragOffset.y;

    setDraggedElement({
      ...draggedElement,
      position: { x, y },
    });
  };

  // Handle touch move for mobile support
  const handleTouchMove = (event) => {
    if (!isDragging || !draggedElement) return;
    event.preventDefault();

    const touch = event.touches[0];
    const workspaceRect = workspaceRef.current.getBoundingClientRect();
    const x = touch.clientX - workspaceRect.left - dragOffset.x;
    const y = touch.clientY - workspaceRect.top - dragOffset.y;

    setDraggedElement({
      ...draggedElement,
      position: { x, y },
    });
  };

  // Handle drop on workspace
  const handleDrop = () => {
    if (!isDragging || !draggedElement) return;

    // Add the element to the workspace
    setWorkspaceElements((prevElements) => [...prevElements, draggedElement]);
    setIsDragging(false);
    setDraggedElement(null);
  };

  // Handle drag start for workspace elements
  const handleWorkspaceElementDragStart = (element, index, event) => {
    if (event.type === "mousedown") {
      const rect = event.currentTarget.getBoundingClientRect();
      setDragOffset({
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      });
    } else {
      setDragOffset({ x: 30, y: 30 });
    }

    setIsDragging(true);
    setDraggedElement({ ...element, index });

    // Remove the element from its current position
    setWorkspaceElements((prevElements) =>
      prevElements.filter((_, i) => i !== index)
    );
  };

  // Handle drop on another workspace element (combination)
  const handleElementDrop = async (targetElement, targetIndex, event) => {
    event.stopPropagation();
    if (!isDragging || !draggedElement) return;

    // Prevent dropping on itself
    if (draggedElement.index === targetIndex) {
      setWorkspaceElements((prevElements) => [
        ...prevElements.slice(0, targetIndex),
        draggedElement,
        ...prevElements.slice(targetIndex),
      ]);
      setIsDragging(false);
      setDraggedElement(null);
      return;
    }
    
    console.log("Attempting to combine elements:", draggedElement, targetElement);

    // Try to combine the elements
    try {
      const userId = localStorage.getItem("infiniteCraftUsername") || "default";
      const response = await fetch(`${BACKEND_URL}/api/elements/combine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          element1_id: draggedElement.id,
          element2_id: targetElement.id,
          user_id: userId,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Show success animation/message
        setCombinationResult({
          success: true,
          result: data.result,
          position: {
            x: targetElement.position.x,
            y: targetElement.position.y,
          },
        });
        setShowResult(true);

        // Clear previous timeout if it exists
        if (resultTimeoutRef.current) {
          clearTimeout(resultTimeoutRef.current);
        }

        // Hide result after 2 seconds
        resultTimeoutRef.current = setTimeout(() => {
          setShowResult(false);
        }, 2000);

        // Remove the target element from workspace
        setWorkspaceElements((prevElements) =>
          prevElements.filter((_, i) => i !== targetIndex)
        );

        // Add the new element to the workspace at the target position
        const newElement = {
          ...data.result,
          workspaceId: generateWorkspaceId(),
          position: targetElement.position,
        };
        setWorkspaceElements((prevElements) => [...prevElements, newElement]);

        // Refresh discovered elements and progress
        fetchDiscoveredElements();
        fetchUserProgress();
      } else {
        // Show failure animation/message
        setCombinationResult({
          success: false,
          message: data.message,
          position: {
            x: targetElement.position.x,
            y: targetElement.position.y,
          },
        });
        setShowResult(true);

        // Clear previous timeout if it exists
        if (resultTimeoutRef.current) {
          clearTimeout(resultTimeoutRef.current);
        }

        // Hide result after 2 seconds
        resultTimeoutRef.current = setTimeout(() => {
          setShowResult(false);
        }, 2000);

        // Put the dragged element back in the workspace
        setWorkspaceElements((prevElements) => [
          ...prevElements,
          {
            ...draggedElement,
            workspaceId: generateWorkspaceId(),
            position: {
              x: targetElement.position.x - 60,
              y: targetElement.position.y,
            },
          },
        ]);
      }
    } catch (error) {
      console.error("Error combining elements:", error);

      // Put the dragged element back in the workspace
      setWorkspaceElements((prevElements) => [
        ...prevElements,
        {
          ...draggedElement,
          workspaceId: generateWorkspaceId(),
          position: {
            x: targetElement.position.x - 60,
            y: targetElement.position.y,
          },
        },
      ]);
    }

    setIsDragging(false);
    setDraggedElement(null);
  };

  // Reset drag state if mouse is released outside workspace
  const handleDragEnd = () => {
    if (isDragging) {
      setIsDragging(false);
      
      // If we were dragging a workspace element and dropped it outside an element,
      // add it back to the workspace
      if (draggedElement && draggedElement.hasOwnProperty('index')) {
        setWorkspaceElements(prev => [
          ...prev, 
          {
            ...draggedElement,
            workspaceId: generateWorkspaceId()
          }
        ]);
      }
      
      setDraggedElement(null);
    }
  };

  const addElementToWorkspace = (element) => {
    // Create a new workspace element in a random position
    const workspaceWidth = workspaceRef.current.clientWidth - 100;
    const workspaceHeight = workspaceRef.current.clientHeight - 100;
    
    const randomX = Math.random() * (workspaceWidth - 200) + 100;
    const randomY = Math.random() * (workspaceHeight - 200) + 100;
    
    const newElement = {
      ...element,
      workspaceId: generateWorkspaceId(),
      position: { x: randomX, y: randomY },
    };
    
    setWorkspaceElements(prev => [...prev, newElement]);
  };

  return (
    <div className="app-container">
      {/* Username Modal */}
      {showUsernameModal && (
        <div className="modal-overlay">
          <div className="username-modal">
            <h2>Welcome to Infinite Craft</h2>
            <p>Please enter your username to begin crafting:</p>
            <form onSubmit={handleUsernameSubmit}>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
              />
              <button type="submit">Start Crafting</button>
            </form>
          </div>
        </div>
      )}

      <div className="header">
        <div className="logo">Infinite Craft</div>
        <div className="user-section">
          {username && <span className="username">👤 {username}</span>}
          <span className="discovery-counter">Discoveries: {discoveryCount}</span>
          <div className="header-buttons">
            <button className="action-button" onClick={clearWorkspace}>
              Clear Workspace
            </button>
            <button className="reset-button" onClick={resetProgress}>
              Reset All
            </button>
          </div>
        </div>
      </div>

      <div className="main-content">
        <div
          className="workspace"
          ref={workspaceRef}
          onMouseMove={handleDragOver}
          onTouchMove={handleTouchMove}
          onMouseUp={handleDrop}
          onTouchEnd={handleDrop}
          onMouseLeave={handleDragEnd}
        >
          {/* Canvas for background animation */}
          <canvas ref={canvasRef} className="workspace-canvas"></canvas>
          
          {/* Workspace elements */}
          {workspaceElements.map((element, index) => (
            <div
              key={element.workspaceId}
              className="element-card workspace-element"
              style={{
                left: `${element.position.x}px`,
                top: `${element.position.y}px`,
              }}
              onMouseDown={(e) => handleWorkspaceElementDragStart(element, index, e)}
              onTouchStart={(e) => handleWorkspaceElementDragStart(element, index, e)}
              onMouseUp={(e) => handleElementDrop(element, index, e)}
              onTouchEnd={(e) => handleElementDrop(element, index, e)}
            >
              <span className="element-emoji">{element.emoji}</span>
              <span className="element-name">{element.name}</span>
            </div>
          ))}

          {/* Currently dragged element */}
          {isDragging && draggedElement && (
            <div
              className="element-card dragging"
              style={{
                left: `${draggedElement.position.x}px`,
                top: `${draggedElement.position.y}px`,
              }}
            >
              <span className="element-emoji">{draggedElement.emoji}</span>
              <span className="element-name">{draggedElement.name}</span>
            </div>
          )}

          {/* Combination result animation */}
          {showResult && combinationResult && (
            <div
              className={`combination-result ${
                combinationResult.success ? "success" : "failure"
              }`}
              style={{
                left: `${combinationResult.position.x}px`,
                top: `${combinationResult.position.y - 40}px`,
              }}
            >
              {combinationResult.success ? (
                <>
                  <span className="result-emoji">
                    {combinationResult.result.emoji}
                  </span>
                  <span className="result-name">
                    {combinationResult.result.name}
                  </span>
                </>
              ) : (
                <span className="result-message">{combinationResult.message}</span>
              )}
            </div>
          )}
        </div>

        <div className="sidebar">
          <div className="sidebar-header">
            <h3>Elements</h3>
          </div>

          <div className="sidebar-content">
            <div className="element-grid">
              {/* Display all elements in a single list */}
              {discoveredElements.map((element) => (
                <div
                  key={element.id}
                  className="element-card"
                  onMouseDown={(e) => handleDragStart(element, e)}
                  onTouchStart={(e) => handleDragStart(element, e)}
                  onClick={() => addElementToWorkspace(element)}
                >
                  <span className="element-emoji">{element.emoji}</span>
                  <span className="element-name">{element.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="instructions">
        <p>
          Drag elements to the workspace and combine them to discover new elements!
          Click on elements to add them directly to the workspace.
        </p>
      </div>
    </div>
  );
}

export default App;
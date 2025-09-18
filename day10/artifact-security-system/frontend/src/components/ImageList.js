import React from 'react';

function ImageList({ images, onRefresh }) {
  return (
    <div className="image-list">
      <div className="list-header">
        <h2>Container Images</h2>
        <button onClick={onRefresh} className="refresh-btn">🔄 Refresh</button>
      </div>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Image</th>
              <th>Tags</th>
              <th>Size</th>
              <th>Security Status</th>
            </tr>
          </thead>
          <tbody>
            {images.map((image, index) => (
              <tr key={index}>
                <td className="image-id">{image.id}</td>
                <td className="tags">
                  {image.tags.slice(0, 2).map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </td>
                <td>{Math.round(image.size / 1024 / 1024)} MB</td>
                <td>
                  <span className={`status-badge ${image.signed ? 'signed' : 'unsigned'}`}>
                    {image.signed ? '🔒 Signed' : '🔓 Unsigned'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ImageList;

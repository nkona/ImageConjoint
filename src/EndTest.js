import React from 'react';
import './App.css';

// Closes out testing ratings and shows recommendations for user
export default class EndTest extends React.Component {

  constructor() {
    super();

    this.state = {
      recs: [],
      userID: 0
    }
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/get_userid', {method: 'GET'} // The type of HTTP request.
    ).then(
      res => {
        // Convert the response data to a JSON.
        return res.json();
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    ).then
      (data => {
        // Act on data
        this.setState({
          // Load the current user's ID
          userID: data.user_id
        });
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    );

    // Send an HTTP request to the server.
    fetch(
      '/load_recs', {method: 'GET'} // The type of HTTP request.
    ).then(
      res => {
        // Convert the response data to a JSON.
        return res.json();
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    ).then
      (data => {
        // Load the current user's recommendations
        console.log(data)
        let item_recs = data.img_urls.map((resultObj, i) =>
        <tr id={"row-" + i}>
          <th scope="row">i</th>
            <img src={resultObj.img_url} className="App-photo" alt="Loading next image..."/>
        </tr>
        );
        this.setState({
          recs: item_recs
        });
      }, err => {
        // Print the error if there is one.
        console.log(err);
      }
    );
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>Thanks for taking our survey! Here are your recommendations: <br></br>
             (For reference, your unique user code is {this.state.userID}) </p>
          <table>
		        <thead></thead>
		        <tbody>
			        {this.state.recs}
		        </tbody>
	        </table>
        </header>
      </div>
    );
  }
}

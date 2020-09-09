import React from 'react';
import {instanceOf} from 'prop-types';
import {withCookies, Cookies} from 'react-cookie';
import './App.css';

// Closes out testing ratings and shows recommendations for user
class EndTest extends React.Component {

  static propTypes = {
    cookies: instanceOf(Cookies).isRequired
  };

  constructor(props) {
    super(props);
    const {cookies} = props;
    this.state = {
      recs: [],
      user: cookies.get('user')
    }
  }

  // React function that is called when the page loads.
  componentDidMount() {
    // Send an HTTP request to the server.
    fetch(
      '/load_recs/' + this.state.user, {method: 'GET'} // The type of HTTP request.
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
             (For reference, your unique user code is {this.state.user}) </p>
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

export default withCookies(EndTest);

// app/javascript/controllers/service_form_controller.js
import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["apiField"];

  connect() {
    this.toggleApiFields();
  }

  toggleApiFields() {
    const serviceType = this.element.querySelector('[name="type"]').value;
    const isApiService = serviceType === "API";

    this.apiFieldTargets.forEach(field => {
      if (isApiService) {
        field.style.display = "block";
      } else {
        field.style.display = "none";
      }
    });
  }
}

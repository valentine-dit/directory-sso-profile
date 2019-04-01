dit = window.dit || {};
dit.components = dit.components || {};

dit.components.expertise = (function() {
  function ExpertiseTypeahead(options) {

    var multiselectElement = options.multiselectElement;
    var addButtonContainerElement = options.addButtonContainerElement;
    var selectedValuesElement = options.selectedValuesElement;
    var noResultsLabel = options.noResultsLabel;
    var autocompleteId = multiselectElement.id + '_autocomplete';
    var containerElement = document.createElement('span');
    multiselectElement.parentNode.insertBefore(containerElement, multiselectElement);

    accessibleAutocomplete({
      element: containerElement,
      selectElement: multiselectElement,
      defaultValue: '',
      confirmOnBlur: false,
      showAllValues: true,
      id: autocompleteId,
      onConfirm: function(confirmed) {
        addButtonContainerElement.style.display = 'block';
      },
      source: function(query, populateResults) {
        var filtered = [].filter.call(
          multiselectElement.options, 
          function(option) { return (option.selected === false)
        });
        var results = filtered
          .map(function(option) { return option.textContent || option.innerText })
          .filter(function(result) { return result.toLowerCase().indexOf(query.toLowerCase()) !== -1 }); 
        populateResults(results);
      }
    });
    multiselectElement.style.display = 'none'
    var autocompleteInputElement = document.getElementById(autocompleteId);
    renderSelectedValues();

    function setOption(label, selected) {
      for (var i = 0; i < multiselectElement.options.length; i++) {
        if (multiselectElement.options[i].innerHTML == label) {
          multiselectElement.options[i].selected = selected;
        }
      }
    }

    function handleAdd() {
      addButtonContainerElement.style.display = 'none';
      setOption(autocompleteInputElement.value, true);
      renderSelectedValues();
      autocompleteInputElement.value = '';
      setTimeout(function() {
        autocompleteInputElement.focus();
      }, 200);
    }

    function handleRemove(event) {
      setOption(event.target.value, false);
      renderSelectedValues();
      autocompleteInputElement.focus();
    }

    function createSelectedValueElement(label) {
      var element = document.createElement('output');
      element.innerHTML = label;
      element.addEventListener('click', handleRemove);
      return element;
    }

    function buildNothingSelectedElement() {
      var element = document.createElement('a');
      element.href = '#' + autocompleteInputElement.id;
      element.class = 'link';
      element.innerHTML = noResultsLabel;
      return element;
    }

    function renderSelectedValues(selectedValues) {
      selectedValuesElement.innerHTML = '';
      var fragment = document.createDocumentFragment();
      for (var i = 0; i < multiselectElement.options.length; i++) {
        var option = multiselectElement.options[i];
        if (option.selected) {
          var element = createSelectedValueElement(option.innerHTML);
          fragment.appendChild(element);
        }
      }
      if (fragment.childNodes.length === 0) {
        var element = buildNothingSelectedElement();
        fragment.appendChild(element);
      }
      selectedValuesElement.appendChild(fragment);
    }
    addButtonContainerElement.addEventListener('click', handleAdd);

  }
  return function(options) {
    return new ExpertiseTypeahead(options);
  }
})();

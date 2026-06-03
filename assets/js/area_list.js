function readInitialGraphState() {
  var element = document.getElementById('initial-graph-state');
  if (!element) {
    return {};
  }

  try {
    return JSON.parse(element.textContent || '{}');
  } catch (error) {
    console.error(error);
    return {};
  }
}

function getModalElement(id) {
  return document.getElementById(id);
}

function showModalElement(element) {
  if (!element) {
    return;
  }

  element.style.display = 'block';
  element.classList.add('show');
}

function hideModalElement(element) {
  if (!element) {
    return;
  }

  element.classList.remove('show');
  element.style.display = 'none';
}

var app = new Vue({
  el: '.app',
  data: {
    minAge: 0,
    maxAge: 100,
    country: '',
    currentGraph: '',
    currentMedian: '',
    currentGraphUuid: '',
    currentExportUrl: '',
    currentAdminUrl: '',
    graphStateSource: '',
    graphModalOpen: false,
    graphZoomed: false,
    graphZoomLocked: false,
    graphZoomHovering: false,
    graphZoomAnchorX: 0.5,
    graphZoomAnchorY: 0.5,
    graphZoomScrollFrame: null,
    graphZoomFrame: null,
    graphImageReady: false,
    graphImageBaseWidth: 0,
    graphImageBaseHeight: 0,
    graphImageZoomWidth: 0,
    graphImageZoomHeight: 0,
    resizeGraphImageHandler: null,
    initialGraphState: {}
  },
  computed: {
    graphImageStyle: function () {
      if (!this.graphImageReady) {
        return {
          visibility: 'visible',
          width: 'auto',
          height: '100%'
        };
      }

      return {
        visibility: 'visible',
        width: (this.graphZoomed ? this.graphImageZoomWidth : this.graphImageBaseWidth) + 'px',
        height: (this.graphZoomed ? this.graphImageZoomHeight : this.graphImageBaseHeight) + 'px'
      };
    }
  },
  watch: {
    graphModalOpen: function (isOpen) {
      document.body.classList.toggle('modal-open', isOpen);
    }
  },
  methods: {
    graphPageUrl: function (uuid) {
      return '/?graph=' + encodeURIComponent(uuid);
    },
    graphExportUrl: function (uuid) {
      return '/graph/' + encodeURIComponent(uuid) + '/export.svg';
    },
    resetModalState: function () {
      this.currentGraph = '';
      this.currentMedian = '';
      this.currentGraphUuid = '';
      this.currentExportUrl = '';
      this.currentAdminUrl = '';
      this.graphStateSource = '';
      this.graphModalOpen = false;
      this.graphZoomed = false;
      this.graphZoomLocked = false;
      this.graphZoomHovering = false;
      this.graphZoomAnchorX = 0.5;
      this.graphZoomAnchorY = 0.5;
      if (this.graphZoomScrollFrame) {
        window.cancelAnimationFrame(this.graphZoomScrollFrame);
        this.graphZoomScrollFrame = null;
      }
      if (this.graphZoomFrame) {
        window.cancelAnimationFrame(this.graphZoomFrame);
        this.graphZoomFrame = null;
      }
      this.graphImageReady = false;
      this.graphImageBaseWidth = 0;
      this.graphImageBaseHeight = 0;
      this.graphImageZoomWidth = 0;
      this.graphImageZoomHeight = 0;
      hideModalElement(getModalElement('graphView'));
    },
    syncHistoryForGraph: function (uuid, title, median, source, replaceState) {
      var state = {
        graphUuid: uuid,
        title: title,
        median: median,
        source: source || 'list'
      };

      if (replaceState) {
        window.history.replaceState(state, '', this.graphPageUrl(uuid));
      } else {
        window.history.pushState(state, '', this.graphPageUrl(uuid));
      }
    },
    openGraph: function (uuid, title, median, options) {
      options = options || {};
      resetIntroTimer();

      this.currentGraph = title;
      this.currentMedian = median;
      this.currentGraphUuid = uuid;
      this.currentExportUrl = this.graphExportUrl(uuid);
      this.currentAdminUrl = options.adminUrl || '';
      this.graphStateSource = options.source || 'list';
      this.graphModalOpen = true;
      this.graphZoomed = false;
      this.graphZoomLocked = false;
      this.graphZoomHovering = false;
      this.graphZoomAnchorX = 0.5;
      this.graphZoomAnchorY = 0.5;
      if (this.graphZoomScrollFrame) {
        window.cancelAnimationFrame(this.graphZoomScrollFrame);
        this.graphZoomScrollFrame = null;
      }
      if (this.graphZoomFrame) {
        window.cancelAnimationFrame(this.graphZoomFrame);
        this.graphZoomFrame = null;
      }
      this.graphImageReady = false;
      this.graphImageBaseWidth = 0;
      this.graphImageBaseHeight = 0;
      this.graphImageZoomWidth = 0;
      this.graphImageZoomHeight = 0;

      var self = this;
      var openModal = function () {
        if (options.updateHistory !== false) {
          self.syncHistoryForGraph(
            uuid,
            title,
            median,
            options.source || 'list',
            Boolean(options.replaceState)
          );
        }
        showModalElement(getModalElement('graphView'));
        self.$nextTick(function () {
          self.refreshGraphImageMetrics(self.$refs.graphImage);
        });
      };
      openModal();
    },
    viewGraph: function (uuid, title, median, adminUrl) {
      this.openGraph(uuid, title, median, {
        source: 'list',
        adminUrl: adminUrl
      });
    },
    hydrateGraphFromUrl: function (graph) {
      this.currentGraph = graph.title;
      this.currentMedian = graph.median;
      this.currentGraphUuid = graph.uuid;
      this.currentExportUrl = graph.export_url || this.graphExportUrl(graph.uuid);
      this.currentAdminUrl = graph.admin_url || '';
      this.graphStateSource = 'direct';
      this.graphModalOpen = true;
      this.graphZoomed = false;
      this.graphZoomLocked = false;
      this.graphZoomHovering = false;
      this.graphZoomAnchorX = 0.5;
      this.graphZoomAnchorY = 0.5;
      if (this.graphZoomScrollFrame) {
        window.cancelAnimationFrame(this.graphZoomScrollFrame);
        this.graphZoomScrollFrame = null;
      }
      if (this.graphZoomFrame) {
        window.cancelAnimationFrame(this.graphZoomFrame);
        this.graphZoomFrame = null;
      }
      this.graphImageReady = false;
      this.graphImageBaseWidth = 0;
      this.graphImageBaseHeight = 0;
      this.graphImageZoomWidth = 0;
      this.graphImageZoomHeight = 0;

      var self = this;
      this.$nextTick(function () {
        showModalElement(getModalElement('graphView'));
        self.refreshGraphImageMetrics(self.$refs.graphImage);
      });
    },
    setGraphZoomHovering: function (isHovering) {
      this.graphZoomHovering = isHovering;
      if (!this.graphZoomLocked) {
        this.graphZoomed = isHovering;
      }
    },
    toggleGraphZoom: function () {
      this.graphZoomLocked = !this.graphZoomLocked;
      this.graphZoomed = this.graphZoomLocked || this.graphZoomHovering;
    },
    updateGraphZoomAnchor: function (event) {
      var panel = event && event.currentTarget;
      if (!panel || typeof panel.getBoundingClientRect !== 'function') {
        return;
      }

      var rect = panel.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }

      var x = (event.clientX - rect.left) / rect.width;
      var y = (event.clientY - rect.top) / rect.height;

      this.graphZoomAnchorX = Math.max(0, Math.min(1, x));
      this.graphZoomAnchorY = Math.max(0, Math.min(1, y));
    },
    handleGraphImageLoad: function (event) {
      this.refreshGraphImageMetrics(event && event.target);
    },
    refreshGraphImageMetrics: function (image) {
      var panel = this.$refs.graphPanel;
      if (!panel || !image || !image.naturalWidth || !image.naturalHeight) {
        return;
      }

      var style = window.getComputedStyle(panel);
      var availableWidth = panel.clientWidth - parseFloat(style.paddingLeft || 0) - parseFloat(style.paddingRight || 0);
      var availableHeight = panel.clientHeight - parseFloat(style.paddingTop || 0) - parseFloat(style.paddingBottom || 0);

      if (availableWidth <= 0 || availableHeight <= 0) {
        return;
      }

      var baseScale = availableHeight / image.naturalHeight;
      var zoomScale = availableWidth / image.naturalWidth;

      this.graphImageBaseWidth = Math.max(1, Math.round(image.naturalWidth * baseScale));
      this.graphImageBaseHeight = Math.max(1, Math.round(availableHeight));
      this.graphImageZoomWidth = Math.max(1, Math.round(availableWidth));
      this.graphImageZoomHeight = Math.max(1, Math.round(image.naturalHeight * zoomScale));
      this.graphImageReady = true;
      if (this.graphZoomed || this.graphZoomLocked) {
        this.scrollGraphToZoomAnchor();
      }
    },
    scrollGraphToZoomAnchor: function () {
      var panel = this.$refs.graphPanel;
      if (!panel) {
        return;
      }

      var maxScrollTop = Math.max(0, panel.scrollHeight - panel.clientHeight);
      var maxScrollLeft = Math.max(0, panel.scrollWidth - panel.clientWidth);
      panel.scrollTop = Math.max(0, Math.min(maxScrollTop, maxScrollTop * this.graphZoomAnchorY));
      panel.scrollLeft = Math.max(0, Math.min(maxScrollLeft, maxScrollLeft * this.graphZoomAnchorX));
    },
    tickGraphZoom: function () {
      if (!this.graphZoomed && !this.graphZoomLocked) {
        if (this.graphZoomFrame) {
          window.cancelAnimationFrame(this.graphZoomFrame);
          this.graphZoomFrame = null;
        }
        return;
      }

      this.scrollGraphToZoomAnchor();
      var self = this;
      this.graphZoomFrame = window.requestAnimationFrame(function () {
        self.tickGraphZoom();
      });
    },
    beginGraphZoom: function (event) {
      this.updateGraphZoomAnchor(event);
      this.graphZoomed = true;
      this.scrollGraphToZoomAnchor();
      this.tickGraphZoom();
    },
    moveGraphZoom: function (event) {
      if (!this.graphZoomed) {
        return;
      }

      this.updateGraphZoomAnchor(event);
      this.scrollGraphToZoomAnchor();
    },
    endGraphZoom: function () {
      if (!this.graphZoomLocked) {
        this.graphZoomed = false;
      }
      if (this.graphZoomFrame) {
        window.cancelAnimationFrame(this.graphZoomFrame);
        this.graphZoomFrame = null;
      }
    },
    closeGraph: function () {
      if (!this.currentGraphUuid) {
        hideModalElement(getModalElement('graphView'));
        this.graphModalOpen = false;
        return;
      }

      if (this.graphStateSource === 'direct') {
        window.history.replaceState(null, '', '/');
        this.resetModalState();
        return;
      }

      window.history.back();
    },
    updateGraphs: function () {
      resetIntroTimer();

      var self = this;
      fetch('/api/area-bios/?minAge=' + encodeURIComponent(this.minAge) +
        '&maxAge=' + encodeURIComponent(this.maxAge) +
        '&country=' + encodeURIComponent(this.country || ''), {credentials: 'same-origin'})
        .then(function (response) {
          return response.json();
        })
        .then(function (bios) {
          var listArea = document.querySelector('.list-area');
          if (!listArea) {
            return;
          }

          listArea.innerHTML = '';

          var chain = Promise.resolve();
          bios.forEach(function (bio) {
            chain = chain.then(function () {
              return fetch('/graph/' + bio.id + '/bare-name/', {credentials: 'same-origin'})
                .then(function (response) {
                  return response.text();
                })
                .then(function (html) {
                  listArea.insertAdjacentHTML('beforeend', html);
                });
            });
          });

          return chain;
        })
        .catch(function (error) {
          console.error(error);
        });
    }
  },
  created: function () {
    this.initialGraphState = readInitialGraphState();
  },
  mounted: function () {
    var self = this;
    this.resizeGraphImageHandler = function () {
      self.refreshGraphImageMetrics(self.$refs.graphImage);
    };
    window.addEventListener('resize', this.resizeGraphImageHandler);

    var graph = this.initialGraphState || {};
    if (!graph.uuid) {
      return;
    }

    this.hydrateGraphFromUrl(graph);
  },
  beforeDestroy: function () {
    if (this.resizeGraphImageHandler) {
      window.removeEventListener('resize', this.resizeGraphImageHandler);
      this.resizeGraphImageHandler = null;
    }
  }
});

window.addEventListener('keydown', function (event) {
  if (event.key === 'Escape' && app.graphModalOpen) {
    app.closeGraph();
  }
});

window.addEventListener('popstate', function (event) {
  var state = event.state || {};

  if (state.graphUuid) {
    app.openGraph(state.graphUuid, state.title, state.median, {
      source: state.source || 'list',
      updateHistory: false
    });
    return;
  }

  app.resetModalState();
});

var element = document.getElementById('age-slider');
var ageSlider = new Slider(element, {
  isDate: false,
  min: 0,
  max: 100,
  start: 0,
  end: 100,
  overlap: true
});
ageSlider.subscribe('moving', function (data) {
  app.minAge = Math.round(data.left);
  app.maxAge = Math.round(data.right);
});
ageSlider.subscribe('stop', function () {
  app.updateGraphs();
});

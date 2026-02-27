import Foundation

#if canImport(ZebraRfidSdkFramework)
import ZebraRfidSdkFramework
#endif

final class NotificationRfidSession: RfidScanSession {
    static let defaultNotificationName = Notification.Name("AssetraRfidScan")

    private let center: NotificationCenter
    private let notificationName: Notification.Name
    private var observer: NSObjectProtocol?

    init(
        center: NotificationCenter = .default,
        notificationName: Notification.Name = NotificationRfidSession.defaultNotificationName
    ) {
        self.center = center
        self.notificationName = notificationName
    }

    func isAvailable() -> Bool {
        true
    }

    func start(onTagRead: @escaping (_ epc: String, _ metadata: [String: String]) -> Void) {
        stop()
        observer = center.addObserver(
            forName: notificationName,
            object: nil,
            queue: .main
        ) { notification in
            guard let userInfo = notification.userInfo else { return }
            let payload = userInfo.reduce(into: [String: String]()) { partial, item in
                partial[String(describing: item.key)] = String(describing: item.value)
            }
            let epc = payload["epc"] ?? payload["tag_id"] ?? payload["data"] ?? payload["raw_value"]
            guard let epc, !epc.isEmpty else { return }

            var metadata = payload
            metadata.removeValue(forKey: "epc")
            metadata.removeValue(forKey: "tag_id")
            metadata.removeValue(forKey: "data")
            metadata.removeValue(forKey: "raw_value")
            onTagRead(epc, metadata)
        }
    }

    func stop() {
        guard let observer else { return }
        center.removeObserver(observer)
        self.observer = nil
    }
}

final class HybridRfidSession: RfidScanSession {
    private let sdkSession: RfidScanSession?
    private let fallbackSession: NotificationRfidSession

    init(
        sdkSession: RfidScanSession? = makeZebraRfidSessionIfAvailable(),
        fallbackSession: NotificationRfidSession = NotificationRfidSession()
    ) {
        self.sdkSession = sdkSession
        self.fallbackSession = fallbackSession
    }

    func isAvailable() -> Bool {
        sdkSession?.isAvailable() == true || fallbackSession.isAvailable()
    }

    func start(onTagRead: @escaping (_ epc: String, _ metadata: [String: String]) -> Void) {
        fallbackSession.start(onTagRead: onTagRead)
        sdkSession?.start(onTagRead: onTagRead)
    }

    func stop() {
        sdkSession?.stop()
        fallbackSession.stop()
    }
}

func makeDefaultRfidSession() -> RfidScanSession {
    HybridRfidSession()
}

#if canImport(ZebraRfidSdkFramework)
private func makeZebraRfidSessionIfAvailable() -> RfidScanSession? {
    let session = ZebraSdkRfidSession()
    return session.isAvailable() ? session : nil
}

private final class ZebraSdkRfidSession: NSObject, RfidScanSession {
    private let api: srfidISdkApi?
    private var delegateProxy: ZebraSdkDelegateProxy?
    private var onTagRead: ((_ epc: String, _ metadata: [String: String]) -> Void)?
    private var connectedReaderID: Int32?

    override init() {
        self.api = srfidSdkFactory.createRfidSdkApiInstance() as? srfidISdkApi
        super.init()
    }

    func isAvailable() -> Bool {
        api != nil
    }

    func start(onTagRead: @escaping (_ epc: String, _ metadata: [String: String]) -> Void) {
        guard let api else { return }
        stop()

        self.onTagRead = onTagRead
        let proxy = ZebraSdkDelegateProxy(owner: self)
        delegateProxy = proxy

        _ = api.srfidSetDelegate(proxy)
        _ = api.srfidSetOperationalMode(Int32(SRFID_OPMODE_ALL))

        let eventMask = Int32(
            SRFID_EVENT_READER_APPEARANCE |
            SRFID_EVENT_SESSION_ESTABLISHMENT |
            SRFID_EVENT_SESSION_TERMINATION |
            SRFID_EVENT_MASK_READ
        )
        _ = api.srfidSubsribeForEvents(eventMask)
        _ = api.srfidEnableAutomaticSessionReestablishment(true)
        _ = api.srfidEnableAvailableReadersDetection(true)

        connectToFirstReaderIfAvailable()
    }

    func stop() {
        guard let api else { return }

        if let readerID = connectedReaderID {
            var statusMessage: NSString?
            _ = api.srfidStopInventory(readerID, aStatusMessage: &statusMessage)
            _ = api.srfidTerminateCommunicationSession(readerID)
        }

        let eventMask = Int32(
            SRFID_EVENT_READER_APPEARANCE |
            SRFID_EVENT_SESSION_ESTABLISHMENT |
            SRFID_EVENT_SESSION_TERMINATION |
            SRFID_EVENT_MASK_READ
        )
        _ = api.srfidUnsubsribeForEvents(eventMask)

        connectedReaderID = nil
        delegateProxy = nil
        onTagRead = nil
    }

    fileprivate func handleReaderAppeared(_ reader: srfidReaderInfo) {
        connect(readerID: Int32(reader.getReaderID()))
    }

    fileprivate func handleSessionEstablished(_ reader: srfidReaderInfo) {
        connectedReaderID = Int32(reader.getReaderID())
        startInventory(readerID: Int32(reader.getReaderID()))
    }

    fileprivate func handleSessionTerminated(_ readerID: Int32) {
        if connectedReaderID == readerID {
            connectedReaderID = nil
        }
    }

    fileprivate func handleTagRead(_ tagData: srfidTagData) {
        let epc = tagData.getTagId().trimmingCharacters(in: .whitespacesAndNewlines)
        guard !epc.isEmpty else { return }

        var metadata: [String: String] = [:]
        metadata["peak_rssi"] = String(tagData.getPeakRSSI())
        metadata["tag_seen_count"] = String(tagData.getTagSeenCount())
        metadata["channel_index"] = String(tagData.getChannelIndex())

        DispatchQueue.main.async { [weak self] in
            self?.onTagRead?(epc, metadata)
        }
    }

    private func connectToFirstReaderIfAvailable() {
        guard let api else { return }

        var activeReaders: NSMutableArray?
        _ = api.srfidGetActiveReadersList(&activeReaders)
        if let reader = (activeReaders?.firstObject as? srfidReaderInfo) {
            connectedReaderID = Int32(reader.getReaderID())
            startInventory(readerID: Int32(reader.getReaderID()))
            return
        }

        var availableReaders: NSMutableArray?
        _ = api.srfidGetAvailableReadersList(&availableReaders)
        if let reader = (availableReaders?.firstObject as? srfidReaderInfo) {
            connect(readerID: Int32(reader.getReaderID()))
        }
    }

    private func connect(readerID: Int32) {
        guard let api else { return }
        _ = api.srfidEstablishCommunicationSession(readerID)
    }

    private func startInventory(readerID: Int32) {
        guard let api else { return }
        var statusMessage: NSString?
        _ = api.srfidStartInventory(
            readerID,
            aMemoryBank: SRFID_MEMORYBANK_NONE,
            aReportConfig: nil,
            aAccessConfig: nil,
            aStatusMessage: &statusMessage
        )
    }
}

private final class ZebraSdkDelegateProxy: NSObject, srfidISdkApiDelegate {
    private weak var owner: ZebraSdkRfidSession?

    init(owner: ZebraSdkRfidSession) {
        self.owner = owner
    }

    func srfidEventReaderAppeared(_ availableReader: srfidReaderInfo!) {
        guard let availableReader else { return }
        owner?.handleReaderAppeared(availableReader)
    }

    func srfidEventReaderDisappeared(_ readerID: Int32) {}

    func srfidEventCommunicationSessionEstablished(_ activeReader: srfidReaderInfo!) {
        guard let activeReader else { return }
        owner?.handleSessionEstablished(activeReader)
    }

    func srfidEventCommunicationSessionTerminated(_ readerID: Int32) {
        owner?.handleSessionTerminated(readerID)
    }

    func srfidEventReadNotify(_ readerID: Int32, aTagData tagData: srfidTagData!) {
        guard let tagData else { return }
        owner?.handleTagRead(tagData)
    }

    func srfidEventStatusNotify(_ readerID: Int32, aEvent event: SRFID_EVENT_STATUS, aNotification notificationData: Any!) {}

    func srfidEventProximityNotify(_ readerID: Int32, aProximityPercent proximityPercent: Int32) {}

    func srfidEventMultiProximityNotify(_ readerID: Int32, aTagData tagData: srfidTagData!) {}

    func srfidEventTriggerNotify(_ readerID: Int32, aTriggerEvent triggerEvent: SRFID_TRIGGEREVENT) {}

    func srfidEventBatteryNotity(_ readerID: Int32, aBatteryEvent batteryEvent: srfidBatteryEvent!) {}

    func srfidEventWifiScan(_ readerID: Int32, wlanSCanObject wlanScanObject: srfidWlanScanList!) {}

    func srfidEventIOTSatusNotity(_ readerID: Int32, aIOTStatusEvent iotStatusEvent: srfidIOTStatusEvent!) {}

    func srfidEventConnectedInterfaceNotity(_ readerID: Int32, aConnectedInterfaceEvent connectedInterfaceEvent: sfidConnectedInterfaceEvent!) {}
}
#else
private func makeZebraRfidSessionIfAvailable() -> RfidScanSession? {
    nil
}
#endif

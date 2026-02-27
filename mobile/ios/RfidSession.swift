import Foundation

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
